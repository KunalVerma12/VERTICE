"""Template discovery, validation, and rendering service."""

import re
from pathlib import Path
from typing import Any
import jinja2
import yaml

from app.core.config import settings
from app.schemas.template import (
    TemplateDetail,
    TemplateSummary,
    TemplateVariable,
)

# Safe naming pattern for templates and services
SAFE_NAME_REGEX = re.compile(r"^[a-zA-Z0-9_-]+$")


class TemplateError(Exception):
    """Base exception for template-related errors."""


class TemplateNotFoundError(TemplateError):
    """Raised when a requested template does not exist."""


class TemplateValidationError(TemplateError):
    """Raised when template metadata or variables fail validation."""


class TemplateSecurityError(TemplateError):
    """Raised when an operation violates security constraints (e.g., path traversal)."""


class TemplateRenderError(TemplateError):
    """Raised when template rendering fails."""


class TemplateService:
    """Service for discovering, validating, and rendering IDP service templates."""

    def __init__(
        self,
        templates_dir: Path | None = None,
        output_dir: Path | None = None,
    ) -> None:
        """Initialize the template service with directory configurations."""
        self.templates_dir = (templates_dir or settings.TEMPLATES_DIR).resolve()
        self.output_dir = (output_dir or settings.OUTPUT_DIR).resolve()

    def _validate_safe_name(self, name: str, field_name: str = "name") -> None:
        """Ensure a name contains only safe alphanumeric characters, dashes, and underscores."""
        if not name or not SAFE_NAME_REGEX.match(name):
            raise TemplateSecurityError(
                f"Invalid {field_name} '{name}': must only contain alphanumeric characters, "
                "dashes, and underscores, without path traversal or separators."
            )

    def _get_template_path(self, template_name: str) -> Path:
        """Resolve and validate the filesystem path for a given template."""
        self._validate_safe_name(template_name, field_name="template_name")

        template_path = (self.templates_dir / template_name).resolve()
        if not str(template_path).startswith(str(self.templates_dir)):
            raise TemplateSecurityError(
                f"Path traversal detected for template '{template_name}'."
            )

        if not template_path.is_dir():
            raise TemplateNotFoundError(
                f"Template '{template_name}' not found."
            )

        return template_path

    def _load_template_metadata(self, template_dir: Path) -> TemplateDetail:
        """Load and parse template.yaml from a template directory."""
        metadata_file = template_dir / "template.yaml"
        if not metadata_file.is_file():
            raise TemplateNotFoundError(
                f"Template metadata file 'template.yaml' missing in '{template_dir.name}'."
            )

        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                raw_data = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise TemplateValidationError(
                f"Failed to parse template.yaml in '{template_dir.name}': {exc}"
            ) from exc

        if not isinstance(raw_data, dict):
            raise TemplateValidationError(
                f"Invalid template.yaml format in '{template_dir.name}': root must be a mapping."
            )

        try:
            variables_data = raw_data.get("variables", []) or []
            variables = [
                TemplateVariable(
                    name=v["name"],
                    required=v.get("required", True),
                    description=v.get("description"),
                    default=v.get("default"),
                )
                for v in variables_data
            ]

            return TemplateDetail(
                name=raw_data.get("name", template_dir.name),
                version=str(raw_data.get("version", "0.1.0")),
                language=raw_data.get("language", "unknown"),
                framework=raw_data.get("framework", "unknown"),
                description=raw_data.get("description", ""),
                variables=variables,
            )
        except (KeyError, TypeError) as exc:
            raise TemplateValidationError(
                f"Invalid template metadata in '{template_dir.name}': {exc}"
            ) from exc

    def list_templates(self) -> list[TemplateSummary]:
        """Discover and list all available templates in the templates directory."""
        if not self.templates_dir.exists() or not self.templates_dir.is_dir():
            return []

        templates: list[TemplateSummary] = []
        for entry in sorted(self.templates_dir.iterdir()):
            if entry.is_dir() and (entry / "template.yaml").is_file():
                try:
                    detail = self._load_template_metadata(entry)
                    templates.append(
                        TemplateSummary(
                            name=detail.name,
                            version=detail.version,
                            language=detail.language,
                            framework=detail.framework,
                            description=detail.description,
                        )
                    )
                except TemplateError:
                    # Skip invalid template directories during listing
                    continue

        return templates

    def get_template(self, template_name: str) -> TemplateDetail:
        """Retrieve detailed metadata for a specific template."""
        template_dir = self._get_template_path(template_name)
        return self._load_template_metadata(template_dir)

    def validate_variables(
        self,
        template_detail: TemplateDetail,
        variables: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate input variables against template definitions and return resolved variables."""
        if not isinstance(variables, dict):
            raise TemplateValidationError("Variables must be provided as a key-value dictionary.")

        resolved_vars: dict[str, Any] = dict(variables)

        # Check required variables and apply defaults
        for var in template_detail.variables:
            if var.name not in resolved_vars or resolved_vars[var.name] is None or resolved_vars[var.name] == "":
                if var.required:
                    raise TemplateValidationError(
                        f"Missing required variable: '{var.name}'."
                    )
                if var.default is not None:
                    resolved_vars[var.name] = var.default

        # Security check on service_name if present
        service_name = resolved_vars.get("service_name")
        if service_name:
            if not isinstance(service_name, str):
                raise TemplateValidationError("Variable 'service_name' must be a string.")
            self._validate_safe_name(service_name, field_name="service_name")

        return resolved_vars

    def render_template(
        self,
        template_name: str,
        variables: dict[str, Any],
        output_base_dir: Path | None = None,
    ) -> Path:
        """Render a template into the target output directory using Jinja2."""
        template_detail = self.get_template(template_name)
        template_dir = self._get_template_path(template_name)
        resolved_vars = self.validate_variables(template_detail, variables)

        service_name = resolved_vars["service_name"]
        base_dir = (output_base_dir or self.output_dir).resolve()
        target_dir = (base_dir / service_name).resolve()

        # Security check: ensure target directory is within base output directory
        if not str(target_dir).startswith(str(base_dir)):
            raise TemplateSecurityError(
                f"Path traversal detected in destination path for service '{service_name}'."
            )

        target_dir.mkdir(parents=True, exist_ok=True)

        jinja_env = jinja2.Environment(
            undefined=jinja2.StrictUndefined,
            keep_trailing_newline=True,
            autoescape=False,
        )

        try:
            for item in template_dir.rglob("*"):
                if item.is_dir():
                    continue

                rel_path = item.relative_to(template_dir)

                # Skip template metadata file
                if rel_path == Path("template.yaml"):
                    continue

                # Render relative path if filename contains variables
                rendered_rel_path_str = jinja_env.from_string(str(rel_path)).render(**resolved_vars)
                dest_file = (target_dir / rendered_rel_path_str).resolve()

                # Security check: ensure destination file is within target directory
                if not str(dest_file).startswith(str(target_dir)):
                    raise TemplateSecurityError(
                        f"Path traversal detected in rendered file destination: '{dest_file}'."
                    )

                dest_file.parent.mkdir(parents=True, exist_ok=True)

                # Try reading and rendering as text file
                try:
                    with open(item, "r", encoding="utf-8") as f:
                        template_content = f.read()

                    rendered_content = jinja_env.from_string(template_content).render(**resolved_vars)

                    with open(dest_file, "w", encoding="utf-8") as f:
                        f.write(rendered_content)

                except UnicodeDecodeError:
                    # Non-text / binary file: copy directly
                    with open(item, "rb") as f_src, open(dest_file, "wb") as f_dst:
                        f_dst.write(f_src.read())

        except jinja2.TemplateError as exc:
            raise TemplateRenderError(f"Jinja2 rendering error: {exc}") from exc
        except Exception as exc:
            if isinstance(exc, TemplateError):
                raise
            raise TemplateRenderError(f"Failed to render template: {exc}") from exc

        return target_dir


template_service = TemplateService()
