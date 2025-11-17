from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional

import backoff
import requests
from pydantic import BaseModel, Field, field_validator


logger = logging.getLogger(__name__)


class NewsCategory(str, Enum):
    """News category classification."""

    COMPANY_SPECIFIC = "company_specific"
    SECTOR_WIDE = "sector_wide"
    MACROECONOMIC = "macroeconomic"
    GEOPOLITICAL = "geopolitical"
    EARNINGS = "earnings"
    REGULATORY = "regulatory"
    MERGER_ACQUISITION = "merger_acquisition"
    GENERAL = "general"


class NewsPriority(str, Enum):
    """News priority levels."""

    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TiingoConfig:
    """Configuration for Tiingo API client."""

    api_key: str
    base_url: str = "https://api.tiingo.com/tiingo"
    rate_limit_requests: int = 500  # requests per hour
    rate_limit_window: int = 3600  # seconds
    timeout: int = 30
    max_retries: int = 3
    session_timeout: int = 300


class TiingoNewsArticle(BaseModel):
    """Structured model for Tiingo news articles."""

    id: str = Field(..., description="Unique article identifier")
    title: str = Field(..., description="Article headline")
    url: str = Field(..., description="Full article URL")
    description: str = Field(..., description="Article summary/description")
    crawl_date: datetime = Field(..., description="When article was crawled")
    published_date: datetime = Field(..., description="Article publication date")
    tickers: list[str] = Field(default_factory=list, description="Related stock tickers")
    tags: list[str] = Field(default_factory=list, description="Article tags")
    source: str = Field(..., description="News source/publication")
    category: NewsCategory | None = Field(None, description="News category classification")
    priority: NewsPriority | None = Field(None, description="Calculated priority level")
    relevance_score: float | None = Field(None, description="Relevance score (0-1)")
    sentiment_score: float | None = Field(None, description="Sentiment score (-1 to 1)")

    @field_validator("crawl_date", "published_date", mode="before")
    @classmethod
    def parse_dates(cls, value):
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                    try:
                        dt_value = datetime.strptime(value, fmt)
                        if dt_value.tzinfo is None:
                            dt_value = dt_value.replace(tzinfo=timezone.utc)
                        return dt_value
                    except ValueError:
                        continue
                raise ValueError(f"Unable to parse date: {value}")
        return value

    @field_validator("relevance_score", "sentiment_score", mode="before")
    @classmethod
    def validate_scores(cls, value):
        if value is not None and not (-1 <= value <= 1):
            raise ValueError("Scores must be between -1 and 1")
        return value


class TiingoNewsResponse(BaseModel):
    """Response model for Tiingo news API."""

    articles: list[TiingoNewsArticle] = Field(default_factory=list)
    total_articles: int = Field(0, description="Total number of articles")
    page: int = Field(1, description="Current page number")
    has_more: bool = Field(False, description="Whether more pages are available")
    request_id: str | None = Field(None, description="Request tracking ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class NewsFilter:
    """Filter parameters for news queries."""

    tickers: list[str] | None = None
    tags: list[str] | None = None
    sources: list[str] | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    categories: list[NewsCategory] | None = None
    min_relevance_score: float | None = None
    priorities: list[NewsPriority] | None = None
    max_articles: int | None = 1000


class RateLimiter:
    """Simple rate limiter for API requests."""

    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: List[datetime] = []
        self._lock = threading.Lock()

    def wait(self):
        with self._lock:
            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(seconds=self.time_window)
            self.calls = [call_time for call_time in self.calls if call_time > cutoff]

            if len(self.calls) >= self.max_calls:
                oldest_call = min(self.calls)
                wait_until = oldest_call + timedelta(seconds=self.time_window)
                wait_time = (wait_until - now).total_seconds()
                if wait_time > 0:
                    logger.info("Tiingo rate limit reached. Sleeping %.1fs", wait_time)
                    time.sleep(wait_time)

            self.calls.append(now)

    def remaining_calls(self) -> int:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=self.time_window)
        recent = [call_time for call_time in self.calls if call_time > cutoff]
        return max(0, self.max_calls - len(recent))


class TiingoNewsClient:
    """Synchronous Tiingo News API client with retry and filtering utilities."""

    def __init__(self, config: TiingoConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Authorization": f"Token {config.api_key}",
                "User-Agent": "TradingAgents/1.0 (Tiingo News Client)",
            }
        )
        self._rate_limiter = RateLimiter(
            max_calls=config.rate_limit_requests,
            time_window=config.rate_limit_window,
        )
        self._request_count = 0

    def close(self):
        self.session.close()

    @backoff.on_exception(
        backoff.expo,
        (requests.RequestException,),
        max_tries=3,
        factor=2,
    )
    def _make_request(self, endpoint: str, params: dict) -> list[dict]:
        self._rate_limiter.wait()
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"

        response = self.session.get(url, params=params, timeout=self.config.timeout)

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            logger.warning("Tiingo rate limit exceeded, waiting %ss", retry_after)
            time.sleep(retry_after)
            raise requests.RequestException("Rate limited by Tiingo")

        if response.status_code == 403:
            raise requests.HTTPError(
                "Tiingo API returned 403 (Forbidden). Verify your TIINGO_API_KEY and plan permissions.",
                response=response,
            )

        response.raise_for_status()

        try:
            data = response.json()
        except ValueError as exc:
            raise requests.RequestException("Tiingo returned invalid JSON") from exc

        if not isinstance(data, list):
            raise requests.RequestException("Unexpected Tiingo payload (expected list).")

        self._request_count += 1
        return data

    def get_news(
        self,
        news_filter: NewsFilter | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> TiingoNewsResponse:
        if news_filter is None:
            news_filter = NewsFilter()

        params = {
            "limit": min(limit, 1000),
            "offset": offset,
        }

        if news_filter.tickers:
            params["tickers"] = ",".join(news_filter.tickers)
        if news_filter.tags:
            params["tags"] = ",".join(news_filter.tags)
        if news_filter.sources:
            params["sources"] = ",".join(news_filter.sources)
        if news_filter.start_date:
            params["startDate"] = news_filter.start_date.strftime("%Y-%m-%d")
        if news_filter.end_date:
            params["endDate"] = news_filter.end_date.strftime("%Y-%m-%d")

        try:
            raw_data = self._make_request("news", params)
        except Exception as exc:
            logger.exception("Failed to fetch Tiingo news: %s", exc)
            return TiingoNewsResponse(
                articles=[],
                total_articles=0,
                timestamp=datetime.now(timezone.utc),
            )

        articles: List[TiingoNewsArticle] = []
        for article_data in raw_data:
            try:
                article = TiingoNewsArticle(**article_data)
                article = self._enhance_article(article)
                if self._passes_filters(article, news_filter):
                    articles.append(article)
            except Exception as exc:
                logger.warning("Failed to process Tiingo article: %s", exc)
                continue

        articles.sort(
            key=lambda article: (
                -(article.relevance_score or 0),
                article.published_date,
            ),
            reverse=True,
        )

        if news_filter.max_articles is not None:
            articles = articles[: news_filter.max_articles]

        return TiingoNewsResponse(
            articles=articles,
            total_articles=len(articles),
            page=(offset // limit) + 1,
            has_more=len(raw_data) == limit,
            timestamp=datetime.now(timezone.utc),
        )

    def _enhance_article(self, article: TiingoNewsArticle) -> TiingoNewsArticle:
        article.category = self._categorize_article(article)
        article.priority = self._calculate_priority(article)
        article.relevance_score = self._calculate_relevance_score(article)
        return article

    def _categorize_article(self, article: TiingoNewsArticle) -> NewsCategory:
        title_lower = article.title.lower()
        description_lower = article.description.lower()
        tags_lower = [tag.lower() for tag in article.tags]

        company_keywords = ["earnings", "revenue", "profit", "loss", "ceo", "cfo", "executive"]
        if any(keyword in title_lower or keyword in description_lower for keyword in company_keywords):
            if any("earning" in tag for tag in tags_lower):
                return NewsCategory.EARNINGS
            return NewsCategory.COMPANY_SPECIFIC

        sector_keywords = ["industry", "sector", "market share", "competition", "regulatory"]
        if any(keyword in title_lower or keyword in description_lower for keyword in sector_keywords):
            return NewsCategory.SECTOR_WIDE

        macro_keywords = ["fed", "interest rate", "inflation", "gdp", "unemployment", "economic"]
        if any(keyword in title_lower or keyword in description_lower for keyword in macro_keywords):
            return NewsCategory.MACROECONOMIC

        geo_keywords = ["war", "sanctions", "trade war", "election", "political", "china", "russia"]
        if any(keyword in title_lower or keyword in description_lower for keyword in geo_keywords):
            return NewsCategory.GEOPOLITICAL

        ma_keywords = ["merger", "acquisition", "takeover", "bought", "acquired", "deal"]
        if any(keyword in title_lower or keyword in description_lower for keyword in ma_keywords):
            return NewsCategory.MERGER_ACQUISITION

        reg_keywords = ["sec", "fda", "regulation", "compliance", "lawsuit", "settlement"]
        if any(keyword in title_lower or keyword in description_lower for keyword in reg_keywords):
            return NewsCategory.REGULATORY

        return NewsCategory.GENERAL

    def _calculate_priority(self, article: TiingoNewsArticle) -> NewsPriority:
        priority_score = 0
        now = datetime.now(timezone.utc)
        age_hours = (now - article.published_date).total_seconds() / 3600

        if age_hours < 1:
            priority_score += 3
        elif age_hours < 6:
            priority_score += 2
        elif age_hours < 24:
            priority_score += 1

        category_scores = {
            NewsCategory.EARNINGS: 3,
            NewsCategory.MERGER_ACQUISITION: 3,
            NewsCategory.REGULATORY: 2,
            NewsCategory.MACROECONOMIC: 2,
            NewsCategory.COMPANY_SPECIFIC: 2,
            NewsCategory.GEOPOLITICAL: 1,
            NewsCategory.SECTOR_WIDE: 1,
            NewsCategory.GENERAL: 0,
        }
        priority_score += category_scores.get(article.category, 0)

        if article.tickers:
            priority_score += min(len(article.tickers), 3)

        urgent_keywords = ["breaking", "urgent", "alert", "emergency", "halt", "suspended"]
        if any(keyword in article.title.lower() for keyword in urgent_keywords):
            priority_score += 4

        if priority_score >= 8:
            return NewsPriority.URGENT
        if priority_score >= 5:
            return NewsPriority.HIGH
        if priority_score >= 2:
            return NewsPriority.MEDIUM
        return NewsPriority.LOW

    def _calculate_relevance_score(self, article: TiingoNewsArticle) -> float:
        score = 0.5
        if article.tickers:
            score += 0.2

        category_relevance = {
            NewsCategory.EARNINGS: 0.3,
            NewsCategory.COMPANY_SPECIFIC: 0.2,
            NewsCategory.MERGER_ACQUISITION: 0.3,
            NewsCategory.REGULATORY: 0.15,
            NewsCategory.MACROECONOMIC: 0.1,
            NewsCategory.SECTOR_WIDE: 0.1,
            NewsCategory.GEOPOLITICAL: 0.05,
            NewsCategory.GENERAL: 0.0,
        }
        score += category_relevance.get(article.category, 0)

        reliable_sources = ["reuters", "bloomberg", "wsj", "ft", "cnbc"]
        if any(source in article.source.lower() for source in reliable_sources):
            score += 0.1

        age_hours = (datetime.now(timezone.utc) - article.published_date).total_seconds() / 3600
        if age_hours < 1:
            score += 0.1
        elif age_hours < 6:
            score += 0.05

        return min(1.0, max(0.0, score))

    def _passes_filters(self, article: TiingoNewsArticle, news_filter: NewsFilter) -> bool:
        if news_filter.categories and article.category not in news_filter.categories:
            return False
        if news_filter.priorities and article.priority not in news_filter.priorities:
            return False
        if (
            news_filter.min_relevance_score is not None
            and (article.relevance_score or 0) < news_filter.min_relevance_score
        ):
            return False
        return True

    def get_request_stats(self) -> dict:
        return {
            "total_requests": self._request_count,
            "rate_limit_remaining": self._rate_limiter.remaining_calls(),
        }


def create_tiingo_client(api_key: str | None = None) -> TiingoNewsClient:
    if api_key is None:
        api_key = os.getenv("TIINGO_API_KEY")
        if not api_key:
            raise ValueError("Tiingo API key must be provided via TIINGO_API_KEY.")
    return TiingoNewsClient(TiingoConfig(api_key=api_key))


_CLIENT: TiingoNewsClient | None = None
_CLIENT_LOCK = threading.Lock()


def _get_client() -> TiingoNewsClient:
    global _CLIENT
    if _CLIENT is None:
        with _CLIENT_LOCK:
            if _CLIENT is None:
                _CLIENT = create_tiingo_client()
    return _CLIENT


def _parse_date(value: str) -> datetime:
    dt_value = datetime.strptime(value, "%Y-%m-%d")
    return dt_value.replace(tzinfo=timezone.utc)


def _serialize_response(
    response: TiingoNewsResponse,
    context: str,
    filters: Dict[str, str],
) -> str:
    payload = {
        "source": "tiingo",
        "context": context,
        "articles": [article.model_dump(mode="json") for article in response.articles],
        "meta": {
            "total_articles": response.total_articles,
            "page": response.page,
            "has_more": response.has_more,
            "request_id": response.request_id,
            "timestamp": response.timestamp.isoformat(),
        },
        "filters": filters,
    }
    return json.dumps(payload)


def get_tiingo_news(ticker: str, start_date: str, end_date: str) -> str:
    client = _get_client()
    start_dt = _parse_date(start_date)
    end_dt = _parse_date(end_date)
    news_filter = NewsFilter(
        tickers=[ticker.upper()],
        start_date=start_dt,
        end_date=end_dt,
        max_articles=200,
    )
    response = client.get_news(news_filter=news_filter, limit=200)
    return _serialize_response(
        response,
        context="ticker",
        filters={
            "symbol": ticker.upper(),
            "start_date": start_date,
            "end_date": end_date,
        },
    )


def get_tiingo_global_news(curr_date: str, look_back_days: int, limit: int) -> str:
    client = _get_client()
    end_dt = _parse_date(curr_date)
    start_dt = end_dt - timedelta(days=look_back_days)
    news_filter = NewsFilter(
        tags=["economy", "macro", "policy"],
        start_date=start_dt,
        end_date=end_dt,
        categories=[
            NewsCategory.MACROECONOMIC,
            NewsCategory.GEOPOLITICAL,
            NewsCategory.REGULATORY,
            NewsCategory.SECTOR_WIDE,
        ],
        max_articles=limit,
    )
    response = client.get_news(news_filter=news_filter, limit=min(limit, 200))
    return _serialize_response(
        response,
        context="macro",
        filters={
            "curr_date": curr_date,
            "look_back_days": str(look_back_days),
            "limit": str(limit),
        },
    )
