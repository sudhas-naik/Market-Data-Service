"""Market data API schemas."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class CandleInterval(str, Enum):
    """Supported candle intervals."""

    ONE_MIN = "1m"
    FIVE_MIN = "5m"
    FIFTEEN_MIN = "15m"
    ONE_HOUR = "1h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"


class QuoteResponse(BaseModel):
    """Latest market quote."""

    symbol: str = Field(..., examples=["AAPL"])
    exchange: str = Field(..., examples=["NASDAQ"])
    price: float = Field(..., examples=[195.20])
    change: float = Field(..., examples=[2.5])
    volume: int = Field(..., examples=[230000])
    timestamp: datetime = Field(..., examples=["2026-06-10T14:30:00Z"])

    model_config = {"json_schema_extra": {"examples": [{
        "symbol": "AAPL",
        "exchange": "NASDAQ",
        "price": 195.20,
        "change": 2.5,
        "volume": 230000,
        "timestamp": "2026-06-10T14:30:00Z",
    }]}}


class OHLCVCandle(BaseModel):
    """Single OHLCV candle."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class CandleQuery(BaseModel):
    """Query parameters for historical candles."""

    symbol: str = Field(..., min_length=1, max_length=20)
    interval: CandleInterval = CandleInterval.ONE_DAY
    from_: datetime = Field(..., alias="from")
    to: datetime

    @field_validator("symbol")
    @classmethod
    def uppercase_symbol(cls, v: str) -> str:
        return v.upper().strip()


class CandleResponse(BaseModel):
    """Historical candle data response."""

    symbol: str
    interval: CandleInterval
    candles: list[OHLCVCandle]


class SearchResult(BaseModel):
    """Symbol search result item."""

    symbol: str
    exchange: str
    company_name: str


class SearchResponse(BaseModel):
    """Symbol search response."""

    query: str
    results: list[SearchResult]
