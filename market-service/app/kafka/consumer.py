"""Extensible Kafka consumer framework."""

import json
from collections.abc import Awaitable, Callable
from typing import Any

from aiokafka import AIOKafkaConsumer

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

MessageHandler = Callable[[dict[str, Any]], Awaitable[None]]


class KafkaConsumerManager:
    """Manages extensible Kafka consumers.

    Register handlers via `register_handler(topic, handler)` and start
    with `start()`. New consumer groups can be added without modifying core code.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._handlers: dict[str, MessageHandler] = {}
        self._consumers: list[AIOKafkaConsumer] = []
        self._running = False

    def register_handler(self, topic: str, handler: MessageHandler) -> None:
        """Register an async handler for a Kafka topic."""
        self._handlers[topic] = handler
        logger.info("kafka_handler_registered", topic=topic)

    async def start(self, group_id: str = "market-service-consumers") -> None:
        """Start consumers for all registered topics."""
        if not self._handlers:
            logger.info("kafka_no_handlers_registered")
            return

        for topic, handler in self._handlers.items():
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=self._settings.kafka_bootstrap_servers,
                group_id=group_id,
                client_id=f"{self._settings.kafka_client_id}-consumer",
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                auto_offset_reset="latest",
            )
            await consumer.start()
            self._consumers.append(consumer)
            logger.info("kafka_consumer_started", topic=topic, group_id=group_id)

        self._running = True

    async def consume_loop(self) -> None:
        """Poll and dispatch messages to registered handlers."""
        while self._running:
            for consumer in self._consumers:
                result = await consumer.getmany(timeout_ms=1000, max_records=10)
                for tp, messages in result.items():
                    handler = self._handlers.get(tp.topic)
                    if handler is None:
                        continue
                    for msg in messages:
                        try:
                            await handler(msg.value)
                        except Exception:
                            logger.exception(
                                "kafka_handler_error",
                                topic=tp.topic,
                                offset=msg.offset,
                            )

    async def stop(self) -> None:
        """Stop all consumers."""
        self._running = False
        for consumer in self._consumers:
            await consumer.stop()
        self._consumers.clear()
        logger.info("kafka_consumers_stopped")
