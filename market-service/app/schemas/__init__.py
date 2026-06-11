"""Pydantic schemas for API request/response models."""

from app.schemas.common import APIResponse, ErrorDetail, ErrorResponse
from app.schemas.market import (
    CandleQuery,
    CandleResponse,
    OHLCVCandle,
    QuoteResponse,
    SearchResult,
    SearchResponse,
)
from app.schemas.watchlist import (
    WatchlistCreate,
    WatchlistItemResponse,
    WatchlistResponse,
)

__all__ = [
    "APIResponse",
    "ErrorDetail",
    "ErrorResponse",
    "QuoteResponse",
    "CandleQuery",
    "CandleResponse",
    "OHLCVCandle",
    "SearchResult",
    "SearchResponse",
    "WatchlistCreate",
    "WatchlistResponse",
    "WatchlistItemResponse",
]
