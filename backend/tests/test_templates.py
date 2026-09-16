"""Tests for template discovery, metadata retrieval, and rendering."""

import shutil
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.template_service import (
    TemplateSecurityError,
    TemplateValidationError,
    TemplateService,
)


@pytest.fixture
def client() -> TestClient:
    """Fixture providing a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def temp_output_dir() -> Path:
    """Fixture providing a temporary directory for rendered template output."""
    temp_dir = Path(tempfile.mkdtemp()).resolve()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_list_templates_returns_available_templates(client: TestClient) -> None:
    """Verify GET /api/v1/templates returns discoverable templates."""
    response = client.get("/api/v1/templates")
    assert response.status_code == 200
    templates = response.json()
    assert isinstance(templates, list)
    assert len(templates) >= 1

    template_names = [t["name"] for t in templates]
    assert "python-fastapi" in template_names

    fastapi_tpl = next(t for t in templates if t["name"] == "python-fastapi")
    assert fastapi_tpl["language"] == "python"
    assert fastapi_tpl["framework"] == "fastapi"
    assert fastapi_tpl["version"] == "1.0.0"


def test_get_existing_template(client: TestClient) -> None:
    """Verify GET /api/v1/templates/{template_name} returns metadata and variables."""
    response = client.get("/api/v1/templates/python-fastapi")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "python-fastapi"
    assert data["language"] == "python"
    assert data["framework"] == "fastapi"
    assert "variables" in data

    var_names = [v["name"] for v in data["variables"]]
    assert "service_name" in var_names
    assert "owner" in var_names
    assert "description" in var_names

    service_name_var = next(v for v in data["variables"] if v["name"] == "service_name")
    assert service_name_var["required"] is True


def test_get_nonexistent_template_returns_404(client: TestClient) -> None:
    """Verify GET /api/v1/templates/nonexistent returns HTTP 404."""
    response = client.get("/api/v1/templates/nonexistent-template")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_render_template_success(client: TestClient, temp_output_dir: Path) -> None:
    """Verify successful template rendering, file generation, and variable substitution."""
    custom_service = TemplateService(output_dir=temp_output_dir)

    rendered_path = custom_service.render_template(
        template_name="python-fastapi",
        variables={
            "service_name": "payment-api",
            "owner": "payments-team",
            "description": "Core payment service",
        },
    )

    assert rendered_path.exists()
    assert rendered_path.is_dir()
    assert rendered_path == (temp_output_dir / "payment-api").resolve()

    # Verify generated files exist
    main_py = rendered_path / "app" / "main.py"
    readme_md = rendered_path / "README.md"
    dockerfile = rendered_path / "Dockerfile"
    requirements_txt = rendered_path / "requirements.txt"
    test_health_py = rendered_path / "tests" / "test_health.py"
    ci_yml = rendered_path / ".github" / "workflows" / "ci.yml"

    assert main_py.exists()
    assert readme_md.exists()
    assert dockerfile.exists()
    assert requirements_txt.exists()
    assert test_health_py.exists()
    assert ci_yml.exists()

    # Verify template.yaml itself was NOT copied to output
    assert not (rendered_path / "template.yaml").exists()

    # Verify variable substitutions
    readme_content = readme_md.read_text(encoding="utf-8")
    assert "# payment-api" in readme_content
    assert "Core payment service" in readme_content
    assert "**Owner**: payments-team" in readme_content
    assert "{{ service_name }}" not in readme_content

    main_content = main_py.read_text(encoding="utf-8")
    assert 'title="payment-api"' in main_content
    assert 'service="payment-api"' in main_content
    assert 'owner="payments-team"' in main_content
    assert "{{ owner }}" not in main_content


def test_render_api_endpoint(client: TestClient) -> None:
    """Verify POST /api/v1/templates/{template_name}/render returns HTTP 200 and metadata."""
    payload = {
        "variables": {
            "service_name": "order-api",
            "owner": "checkout-team",
            "description": "Order placement microservice",
        }
    }
    response = client.post("/api/v1/templates/python-fastapi/render", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["template"] == "python-fastapi"
    assert data["service_name"] == "order-api"
    assert data["status"] == "generated"
    assert "output_path" in data
    assert Path(data["output_path"]).exists()


def test_render_missing_required_variable(client: TestClient) -> None:
    """Verify rendering with missing required variable returns HTTP 400."""
    payload = {
        "variables": {
            "service_name": "order-api",
            # "owner" is required but omitted
        }
    }
    response = client.post("/api/v1/templates/python-fastapi/render", json=payload)
    assert response.status_code == 400
    assert "missing required variable" in response.json()["detail"].lower()


def test_path_traversal_in_template_name_rejected(client: TestClient) -> None:
    """Verify path traversal in template name returns 400."""
    response = client.get("/api/v1/templates/..%2F..%2Fetc")
    assert response.status_code in (400, 404)


def test_path_traversal_in_service_name_rejected(client: TestClient) -> None:
    """Verify path traversal in service_name variable returns HTTP 400."""
    payload = {
        "variables": {
            "service_name": "../../evil-service",
            "owner": "security-tester",
        }
    }
    response = client.post("/api/v1/templates/python-fastapi/render", json=payload)
    assert response.status_code == 400
    assert "invalid service_name" in response.json()["detail"].lower()


def test_service_unit_path_traversal_rejections(temp_output_dir: Path) -> None:
    """Verify TemplateService directly raises security and validation exceptions."""
    service = TemplateService(output_dir=temp_output_dir)

    with pytest.raises(TemplateSecurityError):
        service.get_template("../../secret")

    with pytest.raises(TemplateSecurityError):
        service.render_template(
            "python-fastapi",
            {"service_name": "../traversal", "owner": "test"},
            output_base_dir=temp_output_dir,
        )

    with pytest.raises(TemplateValidationError):
        service.render_template(
            "python-fastapi",
            {"service_name": "test-service"},  # missing owner
            output_base_dir=temp_output_dir,
        )
