"""Watchlist service dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.dependencies.auth import get_current_user_id
from app.repositories.watchlist_repository import WatchlistRepository
from app.services.watchlist_service import WatchlistService


async def get_watchlist_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> WatchlistService:
    return WatchlistService(WatchlistRepository(session))
