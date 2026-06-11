"""Watchlist data access repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.watchlist import Watchlist, WatchlistItem


class WatchlistRepository:
    """Repository for watchlist CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user(self, user_id: str) -> list[Watchlist]:
        result = await self._session.execute(
            select(Watchlist)
            .where(Watchlist.user_id == user_id)
            .options(selectinload(Watchlist.items))
            .order_by(Watchlist.name)
        )
        return list(result.scalars().all())

    async def get_by_id_and_user(self, watchlist_id: int, user_id: str) -> Watchlist | None:
        result = await self._session.execute(
            select(Watchlist)
            .where(Watchlist.id == watchlist_id, Watchlist.user_id == user_id)
            .options(selectinload(Watchlist.items))
        )
        return result.scalar_one_or_none()

    async def get_by_name_and_user(self, name: str, user_id: str) -> Watchlist | None:
        result = await self._session.execute(
            select(Watchlist)
            .where(Watchlist.name == name, Watchlist.user_id == user_id)
            .options(selectinload(Watchlist.items))
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: str, name: str, symbols: list[str]) -> Watchlist:
        watchlist = Watchlist(user_id=user_id, name=name)
        watchlist.items = [WatchlistItem(symbol=s.upper()) for s in symbols]
        self._session.add(watchlist)
        await self._session.flush()
        await self._session.refresh(watchlist)
        return watchlist

    async def update_symbols(self, watchlist: Watchlist, symbols: list[str]) -> Watchlist:
        watchlist.items.clear()
        watchlist.items = [WatchlistItem(symbol=s.upper()) for s in symbols]
        await self._session.flush()
        await self._session.refresh(watchlist)
        return watchlist

    async def remove_symbol_from_user_watchlists(self, user_id: str, symbol: str) -> int:
        """Remove a symbol from all of a user's watchlists. Returns count removed."""
        upper_symbol = symbol.upper()
        user_watchlist_ids = select(Watchlist.id).where(Watchlist.user_id == user_id)
        result = await self._session.execute(
            select(WatchlistItem).where(
                WatchlistItem.watchlist_id.in_(user_watchlist_ids),
                WatchlistItem.symbol == upper_symbol,
            )
        )
        items = list(result.scalars().all())
        for item in items:
            await self._session.delete(item)
        if items:
            await self._session.flush()
        return len(items)

    async def delete(self, watchlist: Watchlist) -> None:
        await self._session.delete(watchlist)
