"""Background worker that refreshes quotes every second."""

import asyncio

from redis.asyncio import Redis

from app.cache.quote_cache import QuoteCache
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.services.market_service import MarketService
from app.services.market_provider import MarketProvider

logger = get_logger(__name__)

# Default symbols to refresh when no watchlist data is available
_DEFAULT_SYMBOLS = ["AAPL", "TSLA", "MSFT", "GOOGL", "AMZN"]


class QuoteRefreshWorker:
    """Periodically fetches latest prices and caches them in Redis."""

    def __init__(
        self,
        provider: MarketProvider,
        redis: Redis,
        settings: Settings | None = None,
        symbols: list[str] | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._service = MarketService(provider, QuoteCache(redis))
        self._symbols = symbols or _DEFAULT_SYMBOLS
        self._interval = self._settings.quote_refresh_interval_seconds
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("quote_refresh_worker_started", interval=self._interval)

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("quote_refresh_worker_stopped")

    async def _run_loop(self) -> None:
        while self._running:
            for symbol in self._symbols:
                try:
                    await self._service.refresh_quote(symbol)
                except Exception:
                    logger.exception("quote_refresh_error", symbol=symbol)
            await asyncio.sleep(self._interval)
