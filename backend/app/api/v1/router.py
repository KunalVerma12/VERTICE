"""API v1 router registry."""

from fastapi import APIRouter
from app.api.v1.endpoints import health, templates

api_router = APIRouter()

# Register endpoint routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(templates.router, prefix="/templates", tags=["Templates"])
