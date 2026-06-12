"""Market news business logic."""

from datetime import datetime

from app.core.logging import get_logger
from app.models.market_news import MarketNews
from app.repositories.market_news_repository import MarketNewsRepository
from app.services.market_provider import MarketProvider

logger = get_logger(__name__)


class NewsService:
    """Fetches and persists market news."""

    def __init__(
        self,
        provider: MarketProvider,
        repository: MarketNewsRepository,
    ) -> None:
        self._provider = provider
        self._repo = repository

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

        logger.info("news_fetched", count=len(stored), symbol=symbol)
        return stored
