"""Market news data access repository."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market_news import MarketNews


class MarketNewsRepository:
    """Repository for market news persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        symbol: str,
        headline: str,
        url: str,
        published_at: datetime,
    ) -> MarketNews:
        news = MarketNews(
            symbol=symbol.upper(),
            headline=headline,
            url=url,
            published_at=published_at,
        )
        self._session.add(news)
        await self._session.flush()
        await self._session.refresh(news)
        return news

    async def get_by_symbol(self, symbol: str, limit: int = 20) -> list[MarketNews]:
        result = await self._session.execute(
            select(MarketNews)
            .where(MarketNews.symbol == symbol.upper())
            .order_by(MarketNews.published_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def bulk_create(self, items: list[MarketNews]) -> list[MarketNews]:
        self._session.add_all(items)
        await self._session.flush()
        return items
