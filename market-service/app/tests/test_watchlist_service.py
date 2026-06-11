"""Tests for WatchlistService."""

import pytest

from app.exceptions.base import AppException
from app.schemas.watchlist import WatchlistCreate


@pytest.mark.asyncio
async def test_create_watchlist(watchlist_service):
    data = WatchlistCreate(name="Tech", symbols=["AAPL", "TSLA"])
    result = await watchlist_service.create_or_update("user-1", data)

    assert result.name == "Tech"
    assert "AAPL" in result.symbols
    assert "TSLA" in result.symbols


@pytest.mark.asyncio
async def test_update_existing_watchlist(watchlist_service):
    data = WatchlistCreate(name="Tech", symbols=["AAPL"])
    await watchlist_service.create_or_update("user-1", data)

    updated = WatchlistCreate(name="Tech", symbols=["MSFT", "GOOGL"])
    result = await watchlist_service.create_or_update("user-1", updated)

    assert set(result.symbols) == {"MSFT", "GOOGL"}


@pytest.mark.asyncio
async def test_list_watchlists(watchlist_service):
    await watchlist_service.create_or_update(
        "user-1", WatchlistCreate(name="Tech", symbols=["AAPL"])
    )
    await watchlist_service.create_or_update(
        "user-1", WatchlistCreate(name="Finance", symbols=["JPM"])
    )

    watchlists = await watchlist_service.list_watchlists("user-1")
    assert len(watchlists) == 2


@pytest.mark.asyncio
async def test_remove_symbol(watchlist_service):
    await watchlist_service.create_or_update(
        "user-1", WatchlistCreate(name="Tech", symbols=["AAPL", "TSLA"])
    )

    result = await watchlist_service.remove_symbol("user-1", "AAPL")
    assert result["removed"] == 1
    assert result["symbol"] == "AAPL"


@pytest.mark.asyncio
async def test_remove_symbol_not_found(watchlist_service):
    with pytest.raises(AppException) as exc_info:
        await watchlist_service.remove_symbol("user-1", "XYZ")

    assert exc_info.value.status_code == 404
