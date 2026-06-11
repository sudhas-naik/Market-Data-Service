"""Market domain event definitions."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class QuoteUpdatedEvent(BaseModel):
    """Emitted when a quote is refreshed."""

    event_type: str = "market.quote.updated"
    symbol: str
    exchange: str
    price: float
    change: float
    volume: int
    timestamp: datetime


class TickEvent(BaseModel):
    """Emitted on each market tick."""

    event_type: str = "market.tick"
    symbol: str
    price: float
    volume: int
    timestamp: datetime


class CandleCompletedEvent(BaseModel):
    """Emitted when a candle interval completes."""

    event_type: str = "market.candle.completed"
    symbol: str
    interval: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    timestamp: datetime


class NewsEvent(BaseModel):
    """Emitted when market news is fetched."""

    event_type: str = "market.news"
    symbol: str
    headline: str
    url: str
    published_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)
