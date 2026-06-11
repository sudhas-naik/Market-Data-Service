"""Integration tests for API endpoints."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.dependencies.market import get_market_service
from app.dependencies.watchlist import get_watchlist_service
from app.db.session import get_db_session
from app.exceptions import SymbolNotFound
from app.repositories.watchlist_repository import WatchlistRepository
from app.schemas.market import CandleInterval, CandleResponse, QuoteResponse, SearchResponse
from app.services.watchlist_service import WatchlistService


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_get_quote_endpoint(test_app, client):
    mock_quote = QuoteResponse(
        symbol="AAPL",
        exchange="NASDAQ",
        price=195.20,
        change=2.5,
        volume=230000,
        timestamp=datetime.now(UTC),
    )
    mock_service = AsyncMock()
    mock_service.get_quote.return_value = mock_quote

    test_app.dependency_overrides[get_market_service] = lambda: mock_service
    try:
        response = await client.get("/market/quote/AAPL")
    finally:
        test_app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["symbol"] == "AAPL"


@pytest.mark.asyncio
async def test_search_endpoint(test_app, client):
    mock_service = AsyncMock()
    mock_service.search_symbols.return_value = SearchResponse(query="app", results=[])

    test_app.dependency_overrides[get_market_service] = lambda: mock_service
    try:
        response = await client.get("/market/search", params={"q": "app"})
    finally:
        test_app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_candles_endpoint(test_app, client):
    mock_service = AsyncMock()
    mock_service.get_candles.return_value = CandleResponse(
        symbol="AAPL",
        interval=CandleInterval.ONE_DAY,
        candles=[],
    )

    test_app.dependency_overrides[get_market_service] = lambda: mock_service
    try:
        response = await client.get(
            "/market/candles",
            params={
                "symbol": "AAPL",
                "interval": "1d",
                "from": "2026-01-01T00:00:00Z",
                "to": "2026-06-01T00:00:00Z",
            },
        )
    finally:
        test_app.dependency_overrides.clear()

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_watchlist_endpoints(test_app, client, db_session):
    async def override_session():
        yield db_session

    service = WatchlistService(WatchlistRepository(db_session))
    test_app.dependency_overrides[get_db_session] = override_session
    test_app.dependency_overrides[get_watchlist_service] = lambda: service

    try:
        create_resp = await client.post(
            "/watchlist",
            json={"name": "Tech", "symbols": ["AAPL", "TSLA"]},
            headers={"X-User-ID": "test-user"},
        )
        assert create_resp.status_code == 201
        assert create_resp.json()["data"]["name"] == "Tech"

        list_resp = await client.get("/watchlist", headers={"X-User-ID": "test-user"})
        assert list_resp.status_code == 200
        assert len(list_resp.json()["data"]) == 1

        delete_resp = await client.delete(
            "/watchlist/AAPL",
            headers={"X-User-ID": "test-user"},
        )
        assert delete_resp.status_code == 200
    finally:
        test_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_symbol_not_found_error(test_app, client):
    mock_service = AsyncMock()
    mock_service.get_quote.side_effect = SymbolNotFound("INVALID")

    test_app.dependency_overrides[get_market_service] = lambda: mock_service
    try:
        response = await client.get("/market/quote/INVALID")
    finally:
        test_app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SYMBOL_NOT_FOUND"
