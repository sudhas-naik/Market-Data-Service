"""Cache related exceptions."""

from app.exceptions.base import AppException


class CacheException(AppException):
    """Raised when Redis cache operations fail."""

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(
            message,
            status_code=503,
            error_code="CACHE_ERROR",
            details=details,
        )
