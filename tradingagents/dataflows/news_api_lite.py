from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import backoff
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.webz.io/newsApiLite"
DEFAULT_MACRO_QUERY = "(economy OR markets OR macroeconomic)"
MAX_POSTS_PER_CALL = 10
RESERVED_CHARS = set(r'+-=!(){}[]^"~*?:\/')


def _current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_timestamp_ms(date_str: str) -> int:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000)


@dataclass
class NewsApiLiteConfig:
    token: str
    timeout: int = 30
    rate_limit_requests: int = 1000  # free tier per month
    rate_limit_window: int = 3600  # simple hourly limiter


class RateLimiter:
    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: List[datetime] = []
        self._lock = threading.Lock()

    def wait(self):
        with self._lock:
            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(seconds=self.time_window)
            self.calls = [call for call in self.calls if call > cutoff]
            if len(self.calls) >= self.max_calls:
                oldest = min(self.calls)
                wait_seconds = (oldest + timedelta(seconds=self.time_window) - now).total_seconds()
                if wait_seconds > 0:
                    time.sleep(wait_seconds)
            self.calls.append(now)


_COMPANY_ALIAS_CACHE: Dict[str, Optional[str]] = {}


def _escape_term(term: str) -> str:
    escaped = []
    for char in term:
        if char in RESERVED_CHARS:
            escaped.append(f"\\{char}")
        else:
            escaped.append(char)
    return "".join(escaped)


def _lookup_company_alias(symbol: str) -> Optional[str]:
    symbol = (symbol or "").upper()
    if not symbol:
        return None
    if symbol in _COMPANY_ALIAS_CACHE:
        return _COMPANY_ALIAS_CACHE[symbol]

    alias = None
    try:
        import yfinance as yf  # Lazy import to avoid slowing startup

        ticker = yf.Ticker(symbol)
        info = ticker.info or {}
        alias = info.get("longName") or info.get("shortName")
    except Exception:
        alias = None

    if alias:
        alias = alias.strip()
    _COMPANY_ALIAS_CACHE[symbol] = alias or None
    return _COMPANY_ALIAS_CACHE[symbol]


class NewsApiLiteClient:
    def __init__(self, config: NewsApiLiteConfig):
        self.config = config
        self.session = requests.Session()
        self._rate_limiter = RateLimiter(config.rate_limit_requests, config.rate_limit_window)

    @backoff.on_exception(backoff.expo, (requests.RequestException,), max_tries=3, factor=2)
    def _get(self, url: str, params: Optional[dict]) -> dict:
        self._rate_limiter.wait()
        response = self.session.get(url, params=params, timeout=self.config.timeout)
        if response.status_code == 401 or response.status_code == 403:
            raise requests.HTTPError(
                "News API Lite rejected the request (check WEBZ_API_TOKEN).",
                response=response,
            )
        response.raise_for_status()
        return response.json()

    def fetch_posts(
        self,
        query: str,
        ts: Optional[int],
        limit: int,
        max_pages: int = 5,
    ) -> Tuple[List[dict], dict]:
        posts: List[dict] = []
        page_meta: Dict[str, Optional[int | str]] = {
            "totalResults": 0,
            "requestsLeft": None,
            "moreResultsAvailable": None,
        }
        next_url: Optional[str] = BASE_URL
        params: Optional[dict] = {
            "token": self.config.token,
            "q": query,
        }
        if ts is not None:
            params["ts"] = ts

        page = 0
        while next_url and page < max_pages and len(posts) < limit:
            data = self._get(next_url, params)
            params = None  # subsequent requests rely on `next` URLs
            page += 1

            batch = data.get("posts") or []
            posts.extend(batch)

            page_meta["totalResults"] = data.get("totalResults", page_meta["totalResults"])
            page_meta["requestsLeft"] = data.get("requestsLeft", page_meta["requestsLeft"])
            page_meta["moreResultsAvailable"] = data.get("moreResultsAvailable", page_meta["moreResultsAvailable"])

            next_url = data.get("next")
            if next_url and not next_url.startswith("http"):
                next_url = urljoin(BASE_URL, next_url)

        return posts[:limit], page_meta


_CLIENT: NewsApiLiteClient | None = None
_CLIENT_LOCK = threading.Lock()


def _client() -> NewsApiLiteClient:
    global _CLIENT
    if _CLIENT is None:
        with _CLIENT_LOCK:
            if _CLIENT is None:
                token = os.getenv("WEBZ_API_TOKEN")
                if not token:
                    raise ValueError("WEBZ_API_TOKEN environment variable is required for News API Lite.")
                _CLIENT = NewsApiLiteClient(NewsApiLiteConfig(token=token))
    return _CLIENT


def _build_query(
    symbol: str,
    start_date: str,
    end_date: str,
    *,
    include_alias: bool = True,
) -> Tuple[str, int, bool]:
    start_ts = _to_timestamp_ms(start_date)
    end_ts = _to_timestamp_ms(end_date) + 24 * 60 * 60 * 1000
    escaped_symbol = _escape_term(symbol.upper())
    search_terms = [
        f'ticker:"{escaped_symbol}"',
        f'"{escaped_symbol}"',
    ]
    alias_used = False
    if include_alias:
        alias = _lookup_company_alias(symbol)
        if alias and alias.lower() != symbol.lower():
            escaped_alias = _escape_term(alias)
            search_terms.extend(
                [
                    f'organization:"{escaped_alias}"',
                    f'"{escaped_alias}"',
                ]
            )
            alias_used = True
    unique_terms: List[str] = []
    seen = set()
    for term in search_terms:
        if term not in seen:
            unique_terms.append(term)
            seen.add(term)
    combined_terms = " OR ".join(unique_terms)
    query = f"({combined_terms}) AND published:>{start_ts} AND published:<{end_ts}"
    return query, start_ts, alias_used


def _build_macro_query(curr_date: str, look_back_days: int) -> Tuple[str, int]:
    end_ts = _to_timestamp_ms(curr_date)
    start_ts = end_ts - look_back_days * 24 * 60 * 60 * 1000
    query = f"{DEFAULT_MACRO_QUERY} AND published:>{start_ts}"
    return query, start_ts


def _transform_post(post: dict) -> dict:
    thread = post.get("thread") or {}
    entities = post.get("entities") or {}
    return {
        "title": post.get("title") or thread.get("title"),
        "url": post.get("url") or thread.get("url"),
        "published": post.get("published"),
        "language": post.get("language"),
        "site": thread.get("site"),
        "country": thread.get("country"),
        "sentiment": post.get("sentiment"),
        "categories": post.get("categories") or thread.get("site_categories"),
        "topics": post.get("topics"),
        "text": post.get("text"),
        "entities": entities,
    }


def _serialize_response(context: str, filters: Dict[str, str], articles: List[dict], meta: dict) -> str:
    payload = {
        "source": "news_api_lite",
        "context": context,
        "filters": filters,
        "articles": [_transform_post(article) for article in articles],
        "meta": {
            "total_results": meta.get("totalResults"),
            "requests_left": meta.get("requestsLeft"),
            "more_results_available": meta.get("moreResultsAvailable"),
            "retrieved": len(articles),
            "timestamp": _current_timestamp(),
        },
    }
    return json.dumps(payload)


def get_news_api_lite(
    ticker: str,
    start_date: str,
    end_date: str,
    *,
    limit: int = 50,
    max_pages: int = 5,
) -> str:
    if not ticker:
        raise ValueError("ticker is required for News API Lite lookups.")

    query, start_ts, alias_used = _build_query(ticker, start_date, end_date)
    client = _client()
    try:
        posts, meta = client.fetch_posts(query, start_ts, limit, max_pages=max_pages)
    except requests.RequestException as exc:
        response = getattr(exc, "response", None)
        status = getattr(response, "status_code", None)
        if alias_used:
            try:
                fallback_query, _, _ = _build_query(
                    ticker, start_date, end_date, include_alias=False
                )
                posts, meta = client.fetch_posts(
                    fallback_query, start_ts, limit, max_pages=max_pages
                )
            except requests.RequestException:
                raise exc
        else:
            raise
    return _serialize_response(
        "ticker",
        {
            "symbol": ticker.upper(),
            "start_date": start_date,
            "end_date": end_date,
        },
        posts,
        meta,
    )


def get_news_api_lite_global(
    curr_date: str,
    look_back_days: int,
    limit: int,
    *,
    max_pages: int = 5,
) -> str:
    query, start_ts = _build_macro_query(curr_date, look_back_days)
    posts, meta = _client().fetch_posts(query, start_ts, limit, max_pages=max_pages)
    return _serialize_response(
        "macro",
        {
            "current_date": curr_date,
            "look_back_days": str(look_back_days),
            "limit": str(limit),
        },
        posts,
        meta,
    )
