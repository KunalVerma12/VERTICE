"""order-api - Main application entrypoint."""

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="order-api",
    description="Order placement microservice",
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
        service="order-api",
        owner="checkout-team",
    )
