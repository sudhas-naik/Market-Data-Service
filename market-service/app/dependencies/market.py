"""Market service dependencies."""

from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis

from app.brokers.factory import get_market_provider
from app.cache.quote_cache import QuoteCache
from app.cache.redis_client import get_redis
from app.dependencies.container import get_kafka_producer_instance
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
        kafka_producer=get_kafka_producer_instance(),
    )
