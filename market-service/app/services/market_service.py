"""Market data business logic."""

import time
from datetime import datetime

from app.cache.quote_cache import QuoteCache
from app.core.logging import get_logger
from app.services.market_provider import MarketProvider
from app.schemas.market import CandleInterval, CandleResponse, QuoteResponse, SearchResponse

logger = get_logger(__name__)


class MarketService:
    """Orchestrates market data retrieval with cache-first strategy."""

    def __init__(
        self,
        provider: MarketProvider,
        cache: QuoteCache,
    ) -> None:
        self._provider = provider
        self._cache = cache

    async def get_quote(self, symbol: str) -> QuoteResponse:
        """Return quote from cache first, fallback to provider."""
        upper_symbol = symbol.upper()

        cached = await self._cache.get(upper_symbol)
        if cached is not None:
            return cached

        start = time.perf_counter()
        quote = await self._provider.get_quote(upper_symbol)
        latency_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "provider_latency",
            provider=type(self._provider).__name__,
            operation="get_quote",
            symbol=upper_symbol,
            latency_ms=round(latency_ms, 2),
        )

        await self._cache.set(quote)
        return quote

    async def refresh_quote(self, symbol: str) -> QuoteResponse:
        """Fetch quote from provider and cache it."""
        start = time.perf_counter()
        quote = await self._provider.get_quote(symbol)
        latency_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "provider_latency",
            provider=type(self._provider).__name__,
            operation="refresh_quote",
            symbol=symbol,
            latency_ms=round(latency_ms, 2),
        )

        await self._cache.set(quote)
        return quote

    async def get_candles(
        self,
        symbol: str,
        interval: CandleInterval,
        from_dt: datetime,
        to_dt: datetime,
    ) -> CandleResponse:
        start = time.perf_counter()
        candles = await self._provider.get_candles(symbol.upper(), interval, from_dt, to_dt)
        latency_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "provider_latency",
            provider=type(self._provider).__name__,
            operation="get_candles",
            symbol=symbol,
            latency_ms=round(latency_ms, 2),
        )

        return CandleResponse(symbol=symbol.upper(), interval=interval, candles=candles)

    async def search_symbols(self, query: str) -> SearchResponse:
        start = time.perf_counter()
        results = await self._provider.search_symbol(query)
        latency_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "provider_latency",
            provider=type(self._provider).__name__,
            operation="search_symbol",
            query=query,
            latency_ms=round(latency_ms, 2),
        )

        return SearchResponse(query=query, results=results)
