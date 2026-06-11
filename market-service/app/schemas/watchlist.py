"""Watchlist API schemas."""

from pydantic import BaseModel, Field, field_validator


class WatchlistCreate(BaseModel):
    """Request body for creating/updating a watchlist."""

    name: str = Field(..., min_length=1, max_length=100, examples=["Tech Stocks"])
    symbols: list[str] = Field(..., min_length=1, examples=[["AAPL", "TSLA", "MSFT"]])

    @field_validator("symbols")
    @classmethod
    def uppercase_symbols(cls, v: list[str]) -> list[str]:
        return [s.upper().strip() for s in v]


class WatchlistItemResponse(BaseModel):
    """Single watchlist item."""

    symbol: str


class WatchlistResponse(BaseModel):
    """Watchlist with items."""

    id: int
    name: str
    symbols: list[str]

    model_config = {"from_attributes": True}
