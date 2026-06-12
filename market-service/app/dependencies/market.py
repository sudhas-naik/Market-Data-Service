"""Market service dependencies."""

from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis

from app.cache.quote_cache import QuoteCache
from app.cache.redis_client import get_redis
from app.services.market_provider import get_market_provider
from app.services.market_service import MarketService


async def get_quote_cache(
    redis: Annotated[Redis, Depends(get_redis)],
) -> QuoteCache:
    return QuoteCache(redis)


async def get_market_service(
    cache: Annotated[QuoteCache, Depends(get_quote_cache)],
) -> MarketService:
    return MarketService(
        provider=get_market_provider(),
        cache=cache,
    )
