"""Tests for Kafka event producer."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.events.market_events import QuoteUpdatedEvent, TickEvent
from app.kafka.producer import KafkaEventProducer


@pytest.mark.asyncio
async def test_publish_quote_updated():
    producer = KafkaEventProducer()
    mock_kafka_producer = AsyncMock()
    mock_kafka_producer.send_and_wait = AsyncMock()
    producer._producer = mock_kafka_producer

    event = QuoteUpdatedEvent(
        symbol="AAPL",
        exchange="NASDAQ",
        price=195.20,
        change=2.5,
        volume=230000,
        timestamp=datetime.now(UTC),
    )

    await producer.publish_quote_updated(event)
    mock_kafka_producer.send_and_wait.assert_called_once()


@pytest.mark.asyncio
async def test_publish_tick():
    producer = KafkaEventProducer()
    mock_kafka_producer = AsyncMock()
    mock_kafka_producer.send_and_wait = AsyncMock()
    producer._producer = mock_kafka_producer

    event = TickEvent(
        symbol="AAPL",
        price=195.20,
        volume=230000,
        timestamp=datetime.now(UTC),
    )

    await producer.publish_tick(event)
    mock_kafka_producer.send_and_wait.assert_called_once()


@pytest.mark.asyncio
async def test_publish_without_start_raises():
    from app.exceptions import KafkaException

    producer = KafkaEventProducer()
    event = TickEvent(
        symbol="AAPL",
        price=100.0,
        volume=1000,
        timestamp=datetime.now(UTC),
    )

    with pytest.raises(KafkaException):
        await producer.publish_tick(event)
