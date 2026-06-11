"""Async Kafka event producer using aiokafka."""

import json
from typing import Any

from aiokafka import AIOKafkaProducer

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.events.market_events import (
    CandleCompletedEvent,
    NewsEvent,
    QuoteUpdatedEvent,
    TickEvent,
)
from app.exceptions import KafkaException

logger = get_logger(__name__)


class KafkaEventProducer:
    """Publishes market domain events to Kafka topics."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        """Initialize and start the Kafka producer."""
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._settings.kafka_bootstrap_servers,
            client_id=self._settings.kafka_client_id,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        )
        await self._producer.start()
        logger.info("kafka_producer_started", servers=self._settings.kafka_bootstrap_servers)

    async def stop(self) -> None:
        """Stop the Kafka producer."""
        if self._producer:
            await self._producer.stop()
            self._producer = None
            logger.info("kafka_producer_stopped")

    async def _publish(self, topic: str, payload: dict[str, Any]) -> None:
        if self._producer is None:
            raise KafkaException("Kafka producer is not started")

        try:
            await self._producer.send_and_wait(topic, payload)
            logger.info("kafka_event_published", topic=topic, event_type=payload.get("event_type"))
        except Exception as exc:
            raise KafkaException(
                f"Failed to publish event to {topic}",
                details={"topic": topic, "error": str(exc)},
            ) from exc

    async def publish_quote_updated(self, event: QuoteUpdatedEvent) -> None:
        await self._publish(
            self._settings.kafka_topic_quote_updated,
            event.model_dump(mode="json"),
        )

    async def publish_tick(self, event: TickEvent) -> None:
        await self._publish(
            self._settings.kafka_topic_tick,
            event.model_dump(mode="json"),
        )

    async def publish_candle_completed(self, event: CandleCompletedEvent) -> None:
        await self._publish(
            self._settings.kafka_topic_candle_completed,
            event.model_dump(mode="json"),
        )

    async def publish_news(self, event: NewsEvent) -> None:
        await self._publish(
            self._settings.kafka_topic_news,
            event.model_dump(mode="json"),
        )
