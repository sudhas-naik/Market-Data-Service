"""Redis connection management."""

from functools import lru_cache

import redis.asyncio as aioredis

from app.core.config import get_settings


@lru_cache
def get_redis_pool() -> aioredis.ConnectionPool:
    """Return a cached Redis connection pool."""
    settings = get_settings()
    return aioredis.ConnectionPool.from_url(
        settings.redis_url,
        decode_responses=True,
        max_connections=20,
    )


async def get_redis() -> aioredis.Redis:
    """Return a Redis client from the shared pool."""
    return aioredis.Redis(connection_pool=get_redis_pool())


async def close_redis() -> None:
    """Close the Redis connection pool on shutdown."""
    pool = get_redis_pool()
    await pool.disconnect()
