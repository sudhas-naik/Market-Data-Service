"""Watchlist business logic."""

from app.exceptions.base import AppException
from app.repositories.watchlist_repository import WatchlistRepository
from app.schemas.watchlist import WatchlistCreate, WatchlistResponse


class WatchlistService:
    """Manages user watchlist operations."""

    def __init__(self, repository: WatchlistRepository) -> None:
        self._repo = repository

    async def create_or_update(self, user_id: str, data: WatchlistCreate) -> WatchlistResponse:
        existing = await self._repo.get_by_name_and_user(data.name, user_id)
        if existing:
            watchlist = await self._repo.update_symbols(existing, data.symbols)
        else:
            watchlist = await self._repo.create(user_id, data.name, data.symbols)

        return self._to_response(watchlist)

    async def list_watchlists(self, user_id: str) -> list[WatchlistResponse]:
        watchlists = await self._repo.get_by_user(user_id)
        return [self._to_response(wl) for wl in watchlists]

    async def remove_symbol(self, user_id: str, symbol: str) -> dict:
        removed = await self._repo.remove_symbol_from_user_watchlists(user_id, symbol)
        if removed == 0:
            raise AppException(
                f"Symbol '{symbol}' not found in any watchlist",
                status_code=404,
                error_code="WATCHLIST_SYMBOL_NOT_FOUND",
                details={"symbol": symbol.upper()},
            )
        return {"removed": removed, "symbol": symbol.upper()}

    @staticmethod
    def _to_response(watchlist) -> WatchlistResponse:
        return WatchlistResponse(
            id=watchlist.id,
            name=watchlist.name,
            symbols=[item.symbol for item in watchlist.items],
        )
