"""Quote caching with Redis."""

import json
from datetime import datetime

from redis.asyncio import Redis

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.exceptions import CacheException
from app.schemas.market import QuoteResponse

logger = get_logger(__name__)


class QuoteCache:
    """Redis-backed cache for latest market quotes.

    Key format: market:{SYMBOL}
    TTL: configurable (default 10 seconds)
    """

    KEY_PREFIX = "market:"

    def __init__(self, redis: Redis, settings: Settings | None = None) -> None:
        self._redis = redis
        self._settings = settings or get_settings()
        self._ttl = self._settings.redis_quote_ttl_seconds

    def _key(self, symbol: str) -> str:
        return f"{self.KEY_PREFIX}{symbol.upper()}"

    async def get(self, symbol: str) -> QuoteResponse | None:
        """Retrieve cached quote. Returns None on cache miss."""
        key = self._key(symbol)
        try:
            raw = await self._redis.get(key)
            if raw is None:
                logger.debug("redis_cache_miss", symbol=symbol, key=key)
                return None

            logger.info("redis_cache_hit", symbol=symbol, key=key)
            data = json.loads(raw)
            if isinstance(data.get("timestamp"), str):
                data["timestamp"] = datetime.fromisoformat(
                    data["timestamp"].replace("Z", "+00:00")
                )
            return QuoteResponse(**data)
        except Exception as exc:
            raise CacheException(
                f"Failed to read quote from cache for {symbol}",
                details={"symbol": symbol, "error": str(exc)},
            ) from exc

    async def set(self, quote: QuoteResponse) -> None:
        """Store quote in cache with TTL."""
        key = self._key(quote.symbol)
        try:
            payload = quote.model_dump(mode="json")
            await self._redis.setex(key, self._ttl, json.dumps(payload))
            logger.debug("redis_cache_set", symbol=quote.symbol, key=key, ttl=self._ttl)
        except Exception as exc:
            raise CacheException(
                f"Failed to write quote to cache for {quote.symbol}",
                details={"symbol": quote.symbol, "error": str(exc)},
            ) from exc

    async def delete(self, symbol: str) -> None:
        """Remove quote from cache."""
        key = self._key(symbol)
        try:
            await self._redis.delete(key)
        except Exception as exc:
            raise CacheException(
                f"Failed to delete quote from cache for {symbol}",
                details={"symbol": symbol, "error": str(exc)},
            ) from exc
