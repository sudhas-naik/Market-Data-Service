"""Authentication related exceptions."""

from app.exceptions.base import AppException


class UnauthorizedException(AppException):
    """Raised when authentication is missing or invalid."""

    def __init__(
        self,
        message: str = "Authentication required",
        *,
        error_code: str = "UNAUTHORIZED",
        details: dict | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=401,
            error_code=error_code,
            details=details,
        )
