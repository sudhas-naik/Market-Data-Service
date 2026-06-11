"""FastAPI dependency injection."""

from app.dependencies.market import get_market_service
from app.dependencies.watchlist import get_watchlist_service

__all__ = ["get_market_service", "get_watchlist_service"]
