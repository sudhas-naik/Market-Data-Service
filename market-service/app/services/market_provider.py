"""Market data providers."""

import asyncio
import csv
import hashlib
import random
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from io import StringIO
from typing import Any

import httpx

from app.core.config import get_settings
from app.exceptions import MarketProviderException, SymbolNotFound
from app.schemas.market import CandleInterval, OHLCVCandle, QuoteResponse, SearchResult

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


class MarketProvider(ABC):
    """Interface for market data sources."""

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
    async def subscribe_ticks(self, symbols: list[str]) -> AsyncIterator[QuoteResponse]:
        """Subscribe to real-time tick updates for given symbols."""

    @abstractmethod
    async def fetch_news(self, symbol: str | None = None) -> list[dict]:
        """Fetch market news, optionally filtered by symbol."""


class MockMarketProvider(MarketProvider):
    """Generates deterministic mock market data."""

    def _base_price(self, symbol: str) -> float:
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
        price = round(base + random.uniform(-2.0, 2.0), 2)  # noqa: S311
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
        seed = self._base_price(symbol)
        candles: list[OHLCVCandle] = []
        current = from_dt

        while current <= to_dt:
            open_p = round(seed + random.uniform(-1, 1), 2)  # noqa: S311
            close_p = round(open_p + random.uniform(-2, 2), 2)  # noqa: S311
            high_p = round(max(open_p, close_p) + random.uniform(0, 1), 2)  # noqa: S311
            low_p = round(min(open_p, close_p) - random.uniform(0, 1), 2)  # noqa: S311
            volume = random.randint(10_000, 500_000)  # noqa: S311

            candles.append(
                OHLCVCandle(
                    timestamp=current,
                    open=open_p,
                    high=high_p,
                    low=low_p,
                    close=close_p,
                    volume=volume,
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
            for symbol in symbols:
                try:
                    yield await self.get_quote(symbol)
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
                news.append(
                    {
                        "symbol": sym,
                        "headline": f"{info['company_name']} reports strong quarterly earnings",
                        "url": f"https://news.example.com/{sym.lower()}/earnings",
                        "published_at": now.isoformat(),
                    }
                )
        return news


class ZerodhaMarketProvider(MarketProvider):
    """Kite Connect market data provider."""

    BASE_URL = "https://api.kite.trade"
    HISTORICAL_INTERVALS = {
        CandleInterval.ONE_MIN: "minute",
        CandleInterval.FIVE_MIN: "5minute",
        CandleInterval.FIFTEEN_MIN: "15minute",
        CandleInterval.ONE_HOUR: "60minute",
        CandleInterval.ONE_DAY: "day",
        CandleInterval.ONE_WEEK: "week",
    }

    def __init__(
        self,
        api_key: str,
        access_token: str | None,
        *,
        default_exchange: str = "NSE",
    ) -> None:
        self._api_key = api_key
        self._access_token = access_token
        self._default_exchange = default_exchange.upper()
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={"X-Kite-Version": "3"},
            timeout=15.0,
        )
        self._instrument_cache: list[dict[str, str]] | None = None
        self._instrument_by_key: dict[str, dict[str, str]] = {}

    def _instrument_key(self, symbol: str) -> str:
        cleaned = symbol.upper().strip()
        if ":" in cleaned:
            return cleaned
        return f"{self._default_exchange}:{cleaned}"

    def _auth_headers(self) -> dict[str, str]:
        if not self._access_token:
            raise MarketProviderException(
                "ZERODHA_ACCESS_TOKEN is required for live Zerodha market data. "
                "Generate it from the daily Zerodha login request token."
            )
        return {"Authorization": f"token {self._api_key}:{self._access_token}"}

    @staticmethod
    def _parse_kite_timestamp(value: str | None) -> datetime:
        if not value:
            return datetime.now(UTC)
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    async def _request(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        try:
            response = await self._client.get(path, params=params, headers=self._auth_headers())
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 403:
                raise MarketProviderException(
                    "Zerodha access token is invalid or expired. Generate a fresh access token.",
                    details={"status_code": exc.response.status_code},
                ) from exc
            if exc.response.status_code == 404:
                raise SymbolNotFound(str(params or path)) from exc
            raise MarketProviderException(
                "Zerodha market data request failed",
                details={"status_code": exc.response.status_code, "body": exc.response.text[:500]},
            ) from exc
        except httpx.HTTPError as exc:
            raise MarketProviderException("Unable to reach Zerodha market data API") from exc

        payload = response.json()
        if payload.get("status") != "success":
            raise MarketProviderException(
                "Zerodha market data request was not successful",
                details={"payload": payload},
            )
        return payload.get("data")

    async def _load_instruments(self) -> list[dict[str, str]]:
        if self._instrument_cache is not None:
            return self._instrument_cache

        try:
            response = await self._client.get("/instruments", headers=self._auth_headers())
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise MarketProviderException("Unable to load Zerodha instrument list") from exc

        instruments = list(csv.DictReader(StringIO(response.text)))
        self._instrument_cache = instruments
        self._instrument_by_key = {
            f"{row.get('exchange', '').upper()}:{row.get('tradingsymbol', '').upper()}": row
            for row in instruments
            if row.get("exchange") and row.get("tradingsymbol")
        }
        return instruments

    async def _get_instrument(self, symbol: str) -> dict[str, str]:
        key = self._instrument_key(symbol)
        await self._load_instruments()
        instrument = self._instrument_by_key.get(key)
        if instrument is None:
            raise SymbolNotFound(symbol)
        return instrument

    async def get_quote(self, symbol: str) -> QuoteResponse:
        key = self._instrument_key(symbol)
        data = await self._request("/quote", params={"i": key})
        quote = data.get(key) if isinstance(data, dict) else None
        if quote is None:
            raise SymbolNotFound(symbol)

        ohlc = quote.get("ohlc") or {}
        price = float(quote.get("last_price") or 0)
        previous_close = float(ohlc.get("close") or price)

        exchange, trading_symbol = key.split(":", 1)
        return QuoteResponse(
            symbol=trading_symbol,
            exchange=exchange,
            price=price,
            change=round(price - previous_close, 2),
            volume=int(quote.get("volume") or 0),
            timestamp=self._parse_kite_timestamp(quote.get("timestamp")),
        )

    async def get_candles(
        self,
        symbol: str,
        interval: CandleInterval,
        from_dt: datetime,
        to_dt: datetime,
    ) -> list[OHLCVCandle]:
        instrument = await self._get_instrument(symbol)
        instrument_token = instrument["instrument_token"]
        kite_interval = self.HISTORICAL_INTERVALS[interval]
        data = await self._request(
            f"/instruments/historical/{instrument_token}/{kite_interval}",
            params={
                "from": from_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "to": to_dt.strftime("%Y-%m-%d %H:%M:%S"),
            },
        )

        return [
            OHLCVCandle(
                timestamp=self._parse_kite_timestamp(candle[0]),
                open=float(candle[1]),
                high=float(candle[2]),
                low=float(candle[3]),
                close=float(candle[4]),
                volume=int(candle[5]),
            )
            for candle in data.get("candles", [])
        ]

    async def search_symbol(self, query: str) -> list[SearchResult]:
        instruments = await self._load_instruments()
        q = query.upper().strip()
        results: list[SearchResult] = []

        for row in instruments:
            symbol = row.get("tradingsymbol", "")
            name = row.get("name", "")
            exchange = row.get("exchange", "")
            if exchange != self._default_exchange:
                continue
            if q in symbol.upper() or q in name.upper():
                results.append(
                    SearchResult(
                        symbol=symbol,
                        exchange=exchange,
                        company_name=name or symbol,
                    )
                )
            if len(results) >= 20:
                break

        return results

    async def subscribe_ticks(self, symbols: list[str]) -> AsyncIterator[QuoteResponse]:
        while True:
            for symbol in symbols:
                try:
                    yield await self.get_quote(symbol)
                except Exception:
                    continue
            await asyncio.sleep(1)

    async def fetch_news(self, symbol: str | None = None) -> list[dict]:
        return []


@lru_cache
def get_market_provider() -> MarketProvider:
    """Return the cached market provider singleton."""
    settings = get_settings()
    if settings.market_provider == "zerodha":
        if not settings.zerodha_api_key:
            raise MarketProviderException(
                "ZERODHA_API_KEY is required when MARKET_PROVIDER=zerodha"
            )
        return ZerodhaMarketProvider(
            api_key=settings.zerodha_api_key,
            access_token=settings.zerodha_access_token,
            default_exchange=settings.zerodha_default_exchange,
        )
    return MockMarketProvider()
