"""Main entrypoint for the Vértice FastAPI application."""

from fastapi import FastAPI
from app.api.v1.router import api_router
from app.core.config import settings


def create_application() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    application = FastAPI(
        title=settings.APP_NAME,
        description=(
            "Vértice is an Internal Developer Platform (IDP) designed to streamline "
            "service management, template orchestration, and developer workflows."
        ),
        version="0.1.0",
        debug=settings.DEBUG,
    )

    # Register API v1 router
    application.include_router(api_router, prefix=settings.API_V1_STR)

    return application


app = create_application()
