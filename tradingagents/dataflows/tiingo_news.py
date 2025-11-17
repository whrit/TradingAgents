from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
from collections.abc import AsyncGenerator, Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, TypeVar

import aiohttp
import backoff
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
    rate_limit_window: int = 3600  # window in seconds
    timeout: int = 30
    max_retries: int = 3
    retry_backoff: float = 2.0
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

    # Enhanced fields for our system
    category: NewsCategory | None = Field(None, description="News category classification")
    priority: NewsPriority | None = Field(None, description="Calculated priority level")
    relevance_score: float | None = Field(None, description="Relevance score (0-1)")
    sentiment_score: float | None = Field(None, description="Sentiment score (-1 to 1)")

    @field_validator("crawl_date", "published_date", mode="before")
    @classmethod
    def parse_dates(cls, v, info):
        """Parse date strings to datetime objects."""
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                    try:
                        dt = datetime.strptime(v, fmt)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        return dt
                    except ValueError:
                        continue
                raise ValueError(f"Unable to parse date: {v}")
        return v

    @field_validator("relevance_score", "sentiment_score", mode="before")
    @classmethod
    def validate_scores(cls, v, info):
        """Validate score ranges."""
        if v is not None and (v < -1 or v > 1):
            raise ValueError("Scores must be between -1 and 1")
        return v


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


class TiingoNewsClient:
    """Advanced Tiingo News API client with comprehensive features."""

    def __init__(self, config: TiingoConfig):
        self.config = config
        self.session: aiohttp.ClientSession | None = None
        self._rate_limiter = RateLimiter(
            max_calls=config.rate_limit_requests,
            time_window=config.rate_limit_window,
        )
        self._request_count = 0
        self._last_reset = datetime.now(timezone.utc)

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {config.api_key}",
            "User-Agent": "TradingAgents/1.0 (Tiingo News Client)",
        }

    async def __aenter__(self):
        await self.start_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()

    async def start_session(self):
        """Initialize HTTP session."""
        if self.session is None:
            connector = aiohttp.TCPConnector(
                limit=20,
                limit_per_host=10,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=60,
            )

            timeout = aiohttp.ClientTimeout(
                total=self.config.timeout,
                connect=10,
            )

            self.session = aiohttp.ClientSession(
                connector=connector,
                headers=self.headers,
                timeout=timeout,
            )

            logger.info("Tiingo News API session initialized")

    async def close_session(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Tiingo News API session closed")

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=3,
        base=2,
        max_time=60,
    )
    async def _make_request(self, endpoint: str, params: dict) -> dict:
        """Make HTTP request with retry logic."""
        if not self.session:
            await self.start_session()

        await self._rate_limiter.wait()

        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"

        try:
            logger.debug("Requesting %s params=%s", url, params)

            async with self.session.get(url, params=params) as response:
                if response.status == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning("Tiingo rate limit exceeded, waiting %ss", retry_after)
                    await asyncio.sleep(retry_after)
                    raise aiohttp.ClientError("Rate limit exceeded")

                if response.status == 401:
                    raise aiohttp.ClientError("Authentication failed - check API key")

                response.raise_for_status()
                data = await response.json()

                self._request_count += 1
                return data

        except aiohttp.ClientError as exc:
            logger.exception("Tiingo request failed: %s", exc)
            raise
        except Exception as exc:
            logger.exception("Unexpected Tiingo error: %s", exc)
            raise aiohttp.ClientError(f"Request failed: {exc}")

    async def get_news(
        self,
        news_filter: NewsFilter | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> TiingoNewsResponse:
        """Retrieve news articles with advanced filtering."""
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
            raw_data = await self._make_request("news", params)
            articles: List[TiingoNewsArticle] = []
            for article_data in raw_data:
                try:
                    article = TiingoNewsArticle(**article_data)
                    article = await self._enhance_article(article)
                    if self._passes_filters(article, news_filter):
                        articles.append(article)
                except Exception as exc:
                    logger.warning("Failed to process Tiingo article: %s", exc)
                    continue

            articles.sort(
                key=lambda x: (
                    -(x.relevance_score or 0),
                    x.published_date,
                ),
                reverse=True,
            )

            if news_filter.max_articles:
                articles = articles[: news_filter.max_articles]

            return TiingoNewsResponse(
                articles=articles,
                total_articles=len(articles),
                page=(offset // limit) + 1,
                has_more=len(raw_data) == limit,
                timestamp=datetime.now(timezone.utc),
            )
        except Exception as exc:
            logger.exception("Failed to fetch Tiingo news: %s", exc)
            return TiingoNewsResponse(
                articles=[],
                total_articles=0,
                timestamp=datetime.now(timezone.utc),
            )

    async def _enhance_article(self, article: TiingoNewsArticle) -> TiingoNewsArticle:
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

        if len(article.tickers) > 0:
            priority_score += min(len(article.tickers), 3)

        urgent_keywords = ["breaking", "urgent", "alert", "emergency", "halt", "suspended"]
        title_lower = article.title.lower()
        if any(keyword in title_lower for keyword in urgent_keywords):
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

    async def get_real_time_news_stream(
        self,
        news_filter: NewsFilter | None = None,
        poll_interval: int = 60,
    ) -> AsyncGenerator[TiingoNewsResponse, None]:
        last_check = datetime.now(timezone.utc) - timedelta(hours=1)

        while True:
            try:
                if news_filter is None:
                    news_filter = NewsFilter()

                news_filter.start_date = last_check
                news_filter.end_date = datetime.now(timezone.utc)

                response = await self.get_news(news_filter, limit=100)

                if response.articles:
                    logger.info("Tiingo stream emitted %s articles", len(response.articles))
                    yield response
                    last_check = max(article.published_date for article in response.articles)

                await asyncio.sleep(poll_interval)

            except Exception as exc:
                logger.exception("Error in Tiingo news stream: %s", exc)
                await asyncio.sleep(poll_interval)
                continue

    async def get_historical_news(
        self,
        start_date: datetime,
        end_date: datetime,
        news_filter: NewsFilter | None = None,
        batch_size: int = 500,
    ) -> AsyncGenerator[TiingoNewsResponse, None]:
        if news_filter is None:
            news_filter = NewsFilter()

        current_date = start_date

        while current_date < end_date:
            batch_end = min(current_date + timedelta(days=7), end_date)

            news_filter.start_date = current_date
            news_filter.end_date = batch_end

            response = await self.get_news(news_filter, limit=batch_size)

            if response.articles:
                logger.info(
                    "Retrieved %s Tiingo articles for %s",
                    len(response.articles),
                    current_date.date(),
                )
                yield response

            current_date = batch_end
            await asyncio.sleep(1)

    def get_request_stats(self) -> dict:
        return {
            "total_requests": self._request_count,
            "session_active": self.session is not None,
            "rate_limit_remaining": self._rate_limiter.remaining_calls(),
            "last_reset": self._last_reset.isoformat(),
        }


class RateLimiter:
    """Simple rate limiter for API requests."""

    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: List[datetime] = []
        self._lock = asyncio.Lock()

    async def wait(self):
        """Wait if rate limit would be exceeded."""
        async with self._lock:
            now = datetime.now()
            cutoff = now - timedelta(seconds=self.time_window)
            self.calls = [call_time for call_time in self.calls if call_time > cutoff]

            if len(self.calls) >= self.max_calls:
                oldest_call = min(self.calls)
                wait_until = oldest_call + timedelta(seconds=self.time_window)
                wait_time = (wait_until - now).total_seconds()

                if wait_time > 0:
                    logger.info("Rate limit reached, sleeping %.1fs", wait_time)
                    await asyncio.sleep(wait_time)

            self.calls.append(now)

    def remaining_calls(self) -> int:
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.time_window)
        recent_calls = [call_time for call_time in self.calls if call_time > cutoff]
        return max(0, self.max_calls - len(recent_calls))


def create_tiingo_client(api_key: str | None = None) -> TiingoNewsClient:
    """Create a configured Tiingo news client."""
    if api_key is None:
        api_key = os.getenv("TIINGO_API_KEY")
        if not api_key:
            raise ValueError("Tiingo API key must be provided via TIINGO_API_KEY")
    config = TiingoConfig(api_key=api_key)
    return TiingoNewsClient(config)


_CLIENT: TiingoNewsClient | None = None
_CLIENT_LOCK = threading.Lock()
_T = TypeVar("_T")


async def _ensure_client() -> TiingoNewsClient:
    global _CLIENT
    if _CLIENT is None:
        with _CLIENT_LOCK:
            if _CLIENT is None:
                _CLIENT = create_tiingo_client()
    await _CLIENT.start_session()
    return _CLIENT


def _run_async(coro_factory: Callable[[], Awaitable[_T]]) -> _T:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro_factory())

    result: Dict[str, _T] = {}
    error: Dict[str, BaseException] = {}

    def _target():
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            result["value"] = new_loop.run_until_complete(coro_factory())
        except BaseException as exc:  # pragma: no cover - defensive
            error["error"] = exc
        finally:
            new_loop.close()

    thread = threading.Thread(target=_target, daemon=True)
    thread.start()
    thread.join()

    if "error" in error:
        raise error["error"]
    return result.get("value")


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


def _parse_date(value: str) -> datetime:
    dt = datetime.strptime(value, "%Y-%m-%d")
    return dt.replace(tzinfo=timezone.utc)


async def _get_tiingo_news_async(ticker: str, start_date: str, end_date: str) -> str:
    client = await _ensure_client()
    start_dt = _parse_date(start_date)
    end_dt = _parse_date(end_date)
    news_filter = NewsFilter(
        tickers=[ticker.upper()],
        start_date=start_dt,
        end_date=end_dt,
        max_articles=200,
    )
    response = await client.get_news(news_filter=news_filter, limit=200)
    return _serialize_response(
        response,
        context="ticker",
        filters={
            "symbol": ticker.upper(),
            "start_date": start_date,
            "end_date": end_date,
        },
    )


async def _get_tiingo_global_news_async(
    curr_date: str,
    look_back_days: int,
    limit: int,
) -> str:
    client = await _ensure_client()
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
    response = await client.get_news(news_filter=news_filter, limit=min(limit, 200))
    return _serialize_response(
        response,
        context="macro",
        filters={
            "curr_date": curr_date,
            "look_back_days": str(look_back_days),
            "limit": str(limit),
        },
    )


def get_tiingo_news(ticker: str, start_date: str, end_date: str) -> str:
    """Public wrapper used by the dataflow interface."""
    return _run_async(lambda: _get_tiingo_news_async(ticker, start_date, end_date))


def get_tiingo_global_news(curr_date: str, look_back_days: int, limit: int) -> str:
    return _run_async(
        lambda: _get_tiingo_global_news_async(curr_date, look_back_days, limit)
    )
