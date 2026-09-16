"""Template registry and rendering API endpoints."""

from fastapi import APIRouter, HTTPException, status
from app.schemas.template import (
    TemplateDetail,
    TemplateRenderRequest,
    TemplateRenderResponse,
    TemplateSummary,
)
from app.services.template_service import (
    TemplateNotFoundError,
    TemplateRenderError,
    TemplateSecurityError,
    TemplateValidationError,
    template_service,
)

router = APIRouter()


@router.get(
    "",
    response_model=list[TemplateSummary],
    summary="List Service Templates",
    description="Discover all available service templates registered in Vértice.",
)
async def list_templates() -> list[TemplateSummary]:
    """Retrieve all discoverable service templates."""
    return template_service.list_templates()


@router.get(
    "/{template_name}",
    response_model=TemplateDetail,
    summary="Get Template Details",
    description="Retrieve detailed metadata and required variables for a specific template.",
)
async def get_template(template_name: str) -> TemplateDetail:
    """Retrieve metadata and variable requirements for a given template."""
    try:
        return template_service.get_template(template_name)
    except TemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except TemplateSecurityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/{template_name}/render",
    response_model=TemplateRenderResponse,
    status_code=status.HTTP_200_OK,
    summary="Render Service Template",
    description="Validate variables and render a service template into a safe target directory.",
)
async def render_template(
    template_name: str,
    payload: TemplateRenderRequest,
) -> TemplateRenderResponse:
    """Render a template with provided variables."""
    try:
        output_path = template_service.render_template(
            template_name=template_name,
            variables=payload.variables,
        )
        service_name = str(payload.variables.get("service_name", ""))
        return TemplateRenderResponse(
            template=template_name,
            service_name=service_name,
            status="generated",
            output_path=str(output_path),
        )
    except TemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except (TemplateValidationError, TemplateSecurityError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except TemplateRenderError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
