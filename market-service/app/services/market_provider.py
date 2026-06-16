"""Market data providers."""

import asyncio
import csv
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from functools import lru_cache
from io import StringIO
from typing import Any

import httpx

from app.core.config import get_settings
from app.exceptions import MarketProviderException, SymbolNotFound
from app.schemas.market import CandleInterval, OHLCVCandle, QuoteResponse, SearchResult


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

from kiteconnect import KiteConnect


@lru_cache
def get_market_provider() -> MarketProvider:
    """Return the cached Zerodha market provider singleton."""
    settings = get_settings()

    if not settings.zerodha_api_key:
        raise MarketProviderException("ZERODHA_API_KEY is required for market data")

    access_token = settings.zerodha_access_token

    # print(f'DEBUG Zerodha access token generated from request token: {access_token[:5]}...')

    if not access_token:
        if not settings.zerodha_api_secret:
            raise MarketProviderException(
                "ZERODHA_API_SECRET is required to generate an access token from "
                "ZERODHA_REQUEST_TOKEN"
            )

        kite = KiteConnect(api_key=settings.zerodha_api_key)

        session = kite.generate_session(
            request_token=settings.zerodha_access_token,
            api_secret=settings.zerodha_api_secret,
        )

        access_token = session["access_token"]

        print(f'DEBUG Zerodha access token generated from request token: {access_token[:5]}...')

    if not access_token:
        raise MarketProviderException(
            "Either ZERODHA_ACCESS_TOKEN or ZERODHA_REQUEST_TOKEN must be provided"
        )

    return ZerodhaMarketProvider(
        api_key=settings.zerodha_api_key,
        access_token=access_token,
        default_exchange=settings.zerodha_default_exchange,
    )
