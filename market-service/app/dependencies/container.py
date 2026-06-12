"""Application-wide dependency container."""

from functools import lru_cache

from app.services.market_provider import get_market_provider


@lru_cache
def get_provider():
    """Cached market provider."""
    return get_market_provider()
