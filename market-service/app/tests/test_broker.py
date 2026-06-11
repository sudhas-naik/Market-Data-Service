"""Tests for market broker providers."""

import pytest

from app.brokers.mock_provider import MockProvider
from app.exceptions import SymbolNotFound
from app.schemas.market import CandleInterval
from datetime import UTC, datetime


@pytest.mark.asyncio
async def test_mock_provider_get_quote():
    provider = MockProvider()
    quote = await provider.get_quote("AAPL")
    assert quote.symbol == "AAPL"
    assert quote.price > 0


@pytest.mark.asyncio
async def test_mock_provider_symbol_not_found():
    provider = MockProvider()
    with pytest.raises(SymbolNotFound):
        await provider.get_quote("NOTAREALSYMBOL123")


@pytest.mark.asyncio
async def test_mock_provider_search():
    provider = MockProvider()
    results = await provider.search_symbol("app")
    assert len(results) >= 1
    assert any(r.symbol == "APP" or "app" in r.company_name.lower() for r in results)


@pytest.mark.asyncio
async def test_mock_provider_candles():
    provider = MockProvider()
    from_dt = datetime(2026, 1, 1, tzinfo=UTC)
    to_dt = datetime(2026, 1, 5, tzinfo=UTC)
    candles = await provider.get_candles("AAPL", CandleInterval.ONE_DAY, from_dt, to_dt)
    assert len(candles) >= 1
