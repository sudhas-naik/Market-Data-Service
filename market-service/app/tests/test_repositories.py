"""Tests for repository layer."""

import pytest
from datetime import UTC, datetime

from app.models.symbol import Symbol
from app.repositories.market_news_repository import MarketNewsRepository
from app.repositories.symbol_repository import SymbolRepository
from app.repositories.watchlist_repository import WatchlistRepository


@pytest.mark.asyncio
async def test_symbol_repository_create_and_search(db_session):
    repo = SymbolRepository(db_session)
    symbol = Symbol(
        symbol="AAPL",
        exchange="NASDAQ",
        company_name="Apple Inc.",
        sector="Technology",
        is_active=True,
    )
    created = await repo.create(symbol)
    await db_session.commit()

    found = await repo.get_by_symbol("AAPL")
    assert found is not None
    assert found.company_name == "Apple Inc."

    results = await repo.search("apple")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_watchlist_repository_crud(db_session):
    repo = WatchlistRepository(db_session)
    wl = await repo.create("user-1", "My List", ["AAPL", "TSLA"])
    await db_session.commit()

    watchlists = await repo.get_by_user("user-1")
    assert len(watchlists) == 1
    assert len(watchlists[0].items) == 2

    removed = await repo.remove_symbol_from_user_watchlists("user-1", "AAPL")
    await db_session.commit()
    assert removed == 1


@pytest.mark.asyncio
async def test_market_news_repository(db_session):
    repo = MarketNewsRepository(db_session)
    news = await repo.create(
        symbol="AAPL",
        headline="Test News",
        url="https://example.com",
        published_at=datetime.now(UTC),
    )
    await db_session.commit()

    results = await repo.get_by_symbol("AAPL")
    assert len(results) == 1
    assert results[0].headline == "Test News"
