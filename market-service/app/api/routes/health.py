"""Health check endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., examples=["healthy"])
    service: str = Field(..., examples=["market-service"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns service health status for load balancers and orchestrators.",
)
async def health_check() -> HealthResponse:
    return HealthResponse(status="healthy", service="market-service")
