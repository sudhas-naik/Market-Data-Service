"""Polygon.io market data provider (stub for future implementation)."""

from collections.abc import AsyncIterator
from datetime import datetime

from app.brokers.base import MarketProvider
from app.exceptions import MarketProviderException
from app.schemas.market import CandleInterval, OHLCVCandle, QuoteResponse, SearchResult


class PolygonProvider(MarketProvider):
    """Polygon.io integration — implement when API keys are configured."""

    async def get_quote(self, symbol: str) -> QuoteResponse:
        raise MarketProviderException("Polygon provider not yet implemented")

    async def get_candles(
        self,
        symbol: str,
        interval: CandleInterval,
        from_dt: datetime,
        to_dt: datetime,
    ) -> list[OHLCVCandle]:
        raise MarketProviderException("Polygon provider not yet implemented")

    async def search_symbol(self, query: str) -> list[SearchResult]:
        raise MarketProviderException("Polygon provider not yet implemented")

    async def subscribe_ticks(self, symbols: list[str]) -> AsyncIterator[QuoteResponse]:
        raise MarketProviderException("Polygon provider not yet implemented")
        yield  # pragma: no cover

    async def fetch_news(self, symbol: str | None = None) -> list[dict]:
        raise MarketProviderException("Polygon provider not yet implemented")
