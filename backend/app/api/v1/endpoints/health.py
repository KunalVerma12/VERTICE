"""Health check endpoint for Vértice API."""

from fastapi import APIRouter
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response payload schema."""

    status: str
    service: str


router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Returns the operational status and service identifier of the Vértice API.",
)
async def get_health() -> HealthResponse:
    """Return service health status."""
    return HealthResponse(
        status="healthy",
        service="vertice-api",
    )
