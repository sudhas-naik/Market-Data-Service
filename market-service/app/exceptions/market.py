"""Market data related exceptions."""

from app.exceptions.base import AppException


class MarketProviderException(AppException):
    """Raised when an external market data provider fails."""

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(
            message,
            status_code=502,
            error_code="MARKET_PROVIDER_ERROR",
            details=details,
        )


class SymbolNotFound(AppException):
    """Raised when a requested symbol does not exist."""

    def __init__(self, symbol: str) -> None:
        super().__init__(
            f"Symbol '{symbol}' not found",
            status_code=404,
            error_code="SYMBOL_NOT_FOUND",
            details={"symbol": symbol},
        )
