"""Background worker that fetches market news every 5 minutes."""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.brokers.base import MarketProvider
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.kafka.producer import KafkaEventProducer
from app.repositories.market_news_repository import MarketNewsRepository
from app.services.news_service import NewsService

logger = get_logger(__name__)


class NewsWorker:
    """Periodically fetches and stores market news."""

    def __init__(
        self,
        provider: MarketProvider,
        session_factory: async_sessionmaker[AsyncSession],
        kafka_producer: KafkaEventProducer,
        settings: Settings | None = None,
    ) -> None:
        self._provider = provider
        self._session_factory = session_factory
        self._kafka = kafka_producer
        self._settings = settings or get_settings()
        self._interval = self._settings.news_fetch_interval_seconds
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("news_worker_started", interval=self._interval)

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("news_worker_stopped")

    async def _run_loop(self) -> None:
        while self._running:
            try:
                async with self._session_factory() as session:
                    service = NewsService(
                        self._provider,
                        MarketNewsRepository(session),
                        self._kafka,
                    )
                    await service.fetch_and_store_news()
                    await session.commit()
            except Exception:
                logger.exception("news_fetch_error")
            await asyncio.sleep(self._interval)
