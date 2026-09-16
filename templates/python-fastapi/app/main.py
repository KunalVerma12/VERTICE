"""{{ service_name }} - Main application entrypoint."""

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="{{ service_name }}",
    description="{{ description }}",
    version="0.1.0",
)


class HealthResponse(BaseModel):
    status: str
    service: str
    owner: str


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Return service health status."""
    return HealthResponse(
        status="healthy",
        service="{{ service_name }}",
        owner="{{ owner }}",
    )
