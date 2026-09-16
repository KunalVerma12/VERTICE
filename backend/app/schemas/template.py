"""Pydantic schemas for template discovery and rendering."""

from typing import Any
from pydantic import BaseModel, Field


class TemplateVariable(BaseModel):
    """Schema defining a template variable requirement."""

    name: str = Field(..., description="Variable name")
    required: bool = Field(default=True, description="Whether the variable is required")
    description: str | None = Field(default=None, description="Explanation of what this variable represents")
    default: Any | None = Field(default=None, description="Default value if not provided")


class TemplateSummary(BaseModel):
    """Schema for template summary in discovery listings."""

    name: str = Field(..., description="Unique template identifier")
    version: str = Field(..., description="Semantic version of the template")
    language: str = Field(..., description="Programming language (e.g., python, javascript)")
    framework: str = Field(..., description="Target framework (e.g., fastapi, express)")
    description: str = Field(..., description="Human-readable description of the template")


class TemplateDetail(TemplateSummary):
    """Schema for detailed template metadata including variable specifications."""

    variables: list[TemplateVariable] = Field(
        default_factory=list,
        description="List of configurable variables supported by the template",
    )


class TemplateRenderRequest(BaseModel):
    """Schema for requesting a template rendering operation."""

    variables: dict[str, Any] = Field(
        ...,
        description="Key-value mapping of variable names to their values",
        examples=[
            {
                "service_name": "payment-api",
                "owner": "payments",
                "description": "Payment processing API",
            }
        ],
    )


class TemplateRenderResponse(BaseModel):
    """Schema for the result of a template rendering operation."""

    template: str = Field(..., description="Name of the rendered template")
    service_name: str = Field(..., description="Name of the generated service")
    status: str = Field(default="generated", description="Generation status")
    output_path: str = Field(..., description="Filesystem path where project was rendered")
