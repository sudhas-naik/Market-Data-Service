"""Watchlist service dependencies."""

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.repositories.watchlist_repository import WatchlistRepository
from app.services.watchlist_service import WatchlistService


def get_current_user_id(request: Request) -> str:
    """Extract user_id injected by upstream JWT middleware."""
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        # Default for development when auth middleware is not present
        return "anonymous"
    return str(user_id)


async def get_watchlist_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> WatchlistService:
    return WatchlistService(WatchlistRepository(session))
