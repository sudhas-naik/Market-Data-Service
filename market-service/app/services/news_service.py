"""Market news business logic."""

from datetime import datetime

from app.brokers.base import MarketProvider
from app.core.logging import get_logger
from app.events.market_events import NewsEvent
from app.kafka.producer import KafkaEventProducer
from app.models.market_news import MarketNews
from app.repositories.market_news_repository import MarketNewsRepository

logger = get_logger(__name__)


class NewsService:
    """Fetches and persists market news."""

    def __init__(
        self,
        provider: MarketProvider,
        repository: MarketNewsRepository,
        kafka_producer: KafkaEventProducer | None = None,
    ) -> None:
        self._provider = provider
        self._repo = repository
        self._kafka = kafka_producer

    async def fetch_and_store_news(self, symbol: str | None = None) -> list[MarketNews]:
        raw_news = await self._provider.fetch_news(symbol)
        stored: list[MarketNews] = []

        for item in raw_news:
            published_at = item["published_at"]
            if isinstance(published_at, str):
                published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))

            news = await self._repo.create(
                symbol=item["symbol"],
                headline=item["headline"],
                url=item["url"],
                published_at=published_at,
            )
            stored.append(news)

            if self._kafka:
                await self._kafka.publish_news(
                    NewsEvent(
                        symbol=item["symbol"],
                        headline=item["headline"],
                        url=item["url"],
                        published_at=published_at,
                    )
                )

        logger.info("news_fetched", count=len(stored), symbol=symbol)
        return stored
