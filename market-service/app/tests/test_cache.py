"""Tests for Redis quote cache."""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.cache.quote_cache import QuoteCache
from app.schemas.market import QuoteResponse


@pytest.fixture
def sample_quote() -> QuoteResponse:
    return QuoteResponse(
        symbol="AAPL",
        exchange="NASDAQ",
        price=195.20,
        change=2.5,
        volume=230000,
        timestamp=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_cache_set(mock_redis, sample_quote):
    cache = QuoteCache(mock_redis)
    await cache.set(sample_quote)

    mock_redis.setex.assert_called_once()
    call_args = mock_redis.setex.call_args
    assert call_args[0][0] == "market:AAPL"


@pytest.mark.asyncio
async def test_cache_get_miss(mock_redis):
    cache = QuoteCache(mock_redis)
    result = await cache.get("AAPL")
    assert result is None


@pytest.mark.asyncio
async def test_cache_get_hit(mock_redis, sample_quote):
    mock_redis.get.return_value = json.dumps(sample_quote.model_dump(mode="json"))
    cache = QuoteCache(mock_redis)
    result = await cache.get("AAPL")

    assert result is not None
    assert result.symbol == "AAPL"
    assert result.price == 195.20
