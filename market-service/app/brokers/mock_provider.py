"""Mock market data provider for development and testing."""

import asyncio
import hashlib
import random
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

from app.brokers.base import MarketProvider
from app.schemas.market import CandleInterval, OHLCVCandle, QuoteResponse, SearchResult

# Seed data for mock provider
_MOCK_SYMBOLS: list[dict[str, str]] = [
    {"symbol": "AAPL", "exchange": "NASDAQ", "company_name": "Apple Inc.", "sector": "Technology"},
    {"symbol": "TSLA", "exchange": "NASDAQ", "company_name": "Tesla Inc.", "sector": "Consumer"},
    {"symbol": "MSFT", "exchange": "NASDAQ", "company_name": "Microsoft Corp.", "sector": "Technology"},
    {"symbol": "GOOGL", "exchange": "NASDAQ", "company_name": "Alphabet Inc.", "sector": "Technology"},
    {"symbol": "AMZN", "exchange": "NASDAQ", "company_name": "Amazon.com Inc.", "sector": "Consumer"},
    {"symbol": "META", "exchange": "NASDAQ", "company_name": "Meta Platforms Inc.", "sector": "Technology"},
    {"symbol": "NVDA", "exchange": "NASDAQ", "company_name": "NVIDIA Corp.", "sector": "Technology"},
    {"symbol": "JPM", "exchange": "NYSE", "company_name": "JPMorgan Chase & Co.", "sector": "Financial"},
    {"symbol": "V", "exchange": "NYSE", "company_name": "Visa Inc.", "sector": "Financial"},
    {"symbol": "APP", "exchange": "NASDAQ", "company_name": "AppLovin Corp.", "sector": "Technology"},
]


class MockProvider(MarketProvider):
    """Generates deterministic mock market data."""

    def _base_price(self, symbol: str) -> float:
        """Derive a stable base price from symbol hash."""
        h = int(hashlib.md5(symbol.encode()).hexdigest()[:8], 16)  # noqa: S324
        return 50.0 + (h % 500)

    def _find_symbol(self, symbol: str) -> dict[str, str] | None:
        upper = symbol.upper()
        return next((s for s in _MOCK_SYMBOLS if s["symbol"] == upper), None)

    async def get_quote(self, symbol: str) -> QuoteResponse:
        info = self._find_symbol(symbol)
        if info is None:
            from app.exceptions import SymbolNotFound

            raise SymbolNotFound(symbol)

        base = self._base_price(symbol)
        jitter = random.uniform(-2.0, 2.0)  # noqa: S311
        price = round(base + jitter, 2)
        change = round(random.uniform(-5.0, 5.0), 2)  # noqa: S311
        volume = random.randint(100_000, 5_000_000)  # noqa: S311

        return QuoteResponse(
            symbol=info["symbol"],
            exchange=info["exchange"],
            price=price,
            change=change,
            volume=volume,
            timestamp=datetime.now(UTC),
        )

    async def get_candles(
        self,
        symbol: str,
        interval: CandleInterval,
        from_dt: datetime,
        to_dt: datetime,
    ) -> list[OHLCVCandle]:
        info = self._find_symbol(symbol)
        if info is None:
            from app.exceptions import SymbolNotFound

            raise SymbolNotFound(symbol)

        interval_map = {
            CandleInterval.ONE_MIN: timedelta(minutes=1),
            CandleInterval.FIVE_MIN: timedelta(minutes=5),
            CandleInterval.FIFTEEN_MIN: timedelta(minutes=15),
            CandleInterval.ONE_HOUR: timedelta(hours=1),
            CandleInterval.ONE_DAY: timedelta(days=1),
            CandleInterval.ONE_WEEK: timedelta(weeks=1),
        }
        step = interval_map[interval]
        base = self._base_price(symbol)
        candles: list[OHLCVCandle] = []
        current = from_dt
        seed = base

        while current <= to_dt:
            open_p = round(seed + random.uniform(-1, 1), 2)  # noqa: S311
            close_p = round(open_p + random.uniform(-2, 2), 2)  # noqa: S311
            high_p = round(max(open_p, close_p) + random.uniform(0, 1), 2)  # noqa: S311
            low_p = round(min(open_p, close_p) - random.uniform(0, 1), 2)  # noqa: S311
            vol = random.randint(10_000, 500_000)  # noqa: S311

            candles.append(
                OHLCVCandle(
                    timestamp=current,
                    open=open_p,
                    high=high_p,
                    low=low_p,
                    close=close_p,
                    volume=vol,
                )
            )
            seed = close_p
            current += step

        return candles

    async def search_symbol(self, query: str) -> list[SearchResult]:
        q = query.lower().strip()
        results = [
            SearchResult(
                symbol=s["symbol"],
                exchange=s["exchange"],
                company_name=s["company_name"],
            )
            for s in _MOCK_SYMBOLS
            if q in s["symbol"].lower() or q in s["company_name"].lower()
        ]
        return results[:20]

    async def subscribe_ticks(self, symbols: list[str]) -> AsyncIterator[QuoteResponse]:
        while True:
            for sym in symbols:
                try:
                    quote = await self.get_quote(sym)
                    yield quote
                except Exception:
                    continue
            await asyncio.sleep(1)

    async def fetch_news(self, symbol: str | None = None) -> list[dict]:
        now = datetime.now(UTC)
        symbols = [symbol.upper()] if symbol else [s["symbol"] for s in _MOCK_SYMBOLS[:5]]
        news = []
        for sym in symbols:
            info = self._find_symbol(sym)
            if info:
                news.append({
                    "symbol": sym,
                    "headline": f"{info['company_name']} reports strong quarterly earnings",
                    "url": f"https://news.example.com/{sym.lower()}/earnings",
                    "published_at": now.isoformat(),
                })
        return news
