"""Unit tests for {{ service_name }} health check."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Fixture providing a test client for the service."""
    return TestClient(app)


def test_health_check(client: TestClient) -> None:
    """Test health check returns expected status and metadata."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "{{ service_name }}",
        "owner": "{{ owner }}",
    }
