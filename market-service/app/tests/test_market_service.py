"""Tests for MarketService."""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.schemas.market import CandleInterval, QuoteResponse


@pytest.mark.asyncio
async def test_get_quote_cache_miss_fetches_provider(market_service, mock_redis, mock_provider):
    quote = await market_service.get_quote("AAPL")

    assert quote.symbol == "AAPL"
    assert quote.price == 100.0
    mock_redis.get.assert_called_once()
    mock_redis.setex.assert_called_once()


@pytest.mark.asyncio
async def test_get_quote_cache_hit(market_service, mock_redis, quote_cache):
    cached_data = QuoteResponse(
        symbol="AAPL",
        exchange="NASDAQ",
        price=195.20,
        change=2.5,
        volume=230000,
        timestamp=datetime.now(UTC),
    )
    mock_redis.get.return_value = json.dumps(cached_data.model_dump(mode="json"))

    quote = await market_service.get_quote("AAPL")
    assert quote.price == 195.20
    mock_redis.setex.assert_not_called()


@pytest.mark.asyncio
async def test_refresh_and_publish_quote(market_service, mock_kafka, mock_redis):
    quote = await market_service.refresh_and_publish_quote("AAPL")

    assert quote.symbol == "AAPL"
    mock_kafka.publish_quote_updated.assert_called_once()
    mock_kafka.publish_tick.assert_called_once()
    mock_redis.setex.assert_called_once()


@pytest.mark.asyncio
async def test_get_candles(market_service):
    from_dt = datetime(2026, 1, 1, tzinfo=UTC)
    to_dt = datetime(2026, 6, 1, tzinfo=UTC)

    result = await market_service.get_candles("AAPL", CandleInterval.ONE_DAY, from_dt, to_dt)

    assert result.symbol == "AAPL"
    assert len(result.candles) == 1
    assert result.candles[0].close == 103.0


@pytest.mark.asyncio
async def test_search_symbols(market_service):
    result = await market_service.search_symbols("app")

    assert result.query == "app"
    assert len(result.results) == 1
    assert result.results[0].symbol == "AAPL"
