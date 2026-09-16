"""Tests for the health check endpoint."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Fixture providing a test client for the FastAPI application."""
    return TestClient(app)


def test_health_check_returns_200_and_expected_data(client: TestClient) -> None:
    """Test that GET /api/v1/health returns 200 and expected response structure."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "vertice-api",
    }
