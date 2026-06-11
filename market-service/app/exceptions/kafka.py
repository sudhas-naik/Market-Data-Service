"""Kafka related exceptions."""

from app.exceptions.base import AppException


class KafkaException(AppException):
    """Raised when Kafka publish/consume operations fail."""

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(
            message,
            status_code=503,
            error_code="KAFKA_ERROR",
            details=details,
        )
