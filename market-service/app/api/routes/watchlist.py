"""Watchlist API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.watchlist import get_current_user_id, get_watchlist_service
from app.schemas.common import APIResponse
from app.schemas.watchlist import WatchlistCreate, WatchlistResponse
from app.services.watchlist_service import WatchlistService

router = APIRouter()


@router.post(
    "",
    response_model=APIResponse[WatchlistResponse],
    status_code=201,
    summary="Create or update watchlist",
    description="Creates a new watchlist or updates an existing one with the same name.",
)
async def create_watchlist(
    data: WatchlistCreate,
    user_id: Annotated[str, Depends(get_current_user_id)],
    service: Annotated[WatchlistService, Depends(get_watchlist_service)],
) -> APIResponse[WatchlistResponse]:
    watchlist = await service.create_or_update(user_id, data)
    return APIResponse(data=watchlist)


@router.get(
    "",
    response_model=APIResponse[list[WatchlistResponse]],
    summary="List watchlists",
    description="Returns all watchlists for the authenticated user.",
)
async def list_watchlists(
    user_id: Annotated[str, Depends(get_current_user_id)],
    service: Annotated[WatchlistService, Depends(get_watchlist_service)],
) -> APIResponse[list[WatchlistResponse]]:
    watchlists = await service.list_watchlists(user_id)
    return APIResponse(data=watchlists)


@router.delete(
    "/{symbol}",
    response_model=APIResponse[dict],
    summary="Remove symbol from watchlists",
    description="Removes a symbol from all of the user's watchlists.",
)
async def remove_symbol(
    symbol: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    service: Annotated[WatchlistService, Depends(get_watchlist_service)],
) -> APIResponse[dict]:
    result = await service.remove_symbol(user_id, symbol)
    return APIResponse(data=result)
