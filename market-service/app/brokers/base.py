"""Abstract market data provider interface."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import datetime

from app.schemas.market import CandleInterval, OHLCVCandle, QuoteResponse, SearchResult


class MarketProvider(ABC):
    """Pluggable interface for external market data sources.

    Implementations: MockProvider, PolygonProvider, AlpacaProvider, etc.
    """

    @abstractmethod
    async def get_quote(self, symbol: str) -> QuoteResponse:
        """Fetch the latest quote for a symbol."""

    @abstractmethod
    async def get_candles(
        self,
        symbol: str,
        interval: CandleInterval,
        from_dt: datetime,
        to_dt: datetime,
    ) -> list[OHLCVCandle]:
        """Fetch historical OHLCV candles."""

    @abstractmethod
    async def search_symbol(self, query: str) -> list[SearchResult]:
        """Search for symbols matching a query string."""

    @abstractmethod
    async def subscribe_ticks(
        self,
        symbols: list[str],
    ) -> AsyncIterator[QuoteResponse]:
        """Subscribe to real-time tick updates for given symbols."""

    @abstractmethod
    async def fetch_news(self, symbol: str | None = None) -> list[dict]:
        """Fetch market news, optionally filtered by symbol."""
