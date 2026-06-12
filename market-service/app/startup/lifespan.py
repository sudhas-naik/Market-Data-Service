"""FastAPI lifespan manager for startup/shutdown."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.cache.redis_client import close_redis, get_redis
from app.core.logging import get_logger
from app.db.session import async_session_factory
from app.services.market_provider import get_market_provider
from app.workers.news_worker import NewsWorker
from app.workers.quote_refresh_worker import QuoteRefreshWorker

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle: workers and connections."""
    quote_worker: QuoteRefreshWorker | None = None
    news_worker: NewsWorker | None = None

    try:
        redis = await get_redis()
        provider = get_market_provider()

        quote_worker = QuoteRefreshWorker(provider, redis)
        news_worker = NewsWorker(provider, async_session_factory)

        await quote_worker.start()
        await news_worker.start()

        logger.info("application_started")
        yield
    finally:
        if quote_worker:
            await quote_worker.stop()
        if news_worker:
            await news_worker.stop()

        await close_redis()
        logger.info("application_stopped")
