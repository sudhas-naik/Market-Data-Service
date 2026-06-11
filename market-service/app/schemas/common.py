"""Common API response schemas."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Standard error detail payload."""

    code: str = Field(..., examples=["SYMBOL_NOT_FOUND"])
    message: str = Field(..., examples=["Symbol 'XYZ' not found"])
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standard error response envelope."""

    success: bool = False
    error: ErrorDetail


class APIResponse(BaseModel, Generic[T]):
    """Standard success response envelope."""

    success: bool = True
    data: T
