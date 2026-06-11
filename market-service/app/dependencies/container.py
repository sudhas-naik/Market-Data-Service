"""Application-wide dependency container."""

from functools import lru_cache

from app.brokers.factory import get_market_provider
from app.kafka.producer import KafkaEventProducer

_kafka_producer: KafkaEventProducer | None = None


def get_kafka_producer_instance() -> KafkaEventProducer | None:
    """Return the global Kafka producer if initialized."""
    return _kafka_producer


def set_kafka_producer_instance(producer: KafkaEventProducer | None) -> None:
    """Set the global Kafka producer (called during startup)."""
    global _kafka_producer  # noqa: PLW0603
    _kafka_producer = producer


@lru_cache
def get_provider():
    """Cached market provider."""
    return get_market_provider()
