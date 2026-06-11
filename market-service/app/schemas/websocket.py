"""WebSocket message schemas."""

from pydantic import BaseModel, Field, field_validator


class SubscribeMessage(BaseModel):
    """Client subscription message."""

    symbols: list[str] = Field(..., min_length=1, examples=[["AAPL", "TSLA", "MSFT"]])

    @field_validator("symbols")
    @classmethod
    def uppercase_symbols(cls, v: list[str]) -> list[str]:
        return [s.upper().strip() for s in v]


class QuotePushMessage(BaseModel):
    """Server push message for live quotes."""

    type: str = "quote"
    symbol: str
    exchange: str
    price: float
    change: float
    volume: int
    timestamp: str
