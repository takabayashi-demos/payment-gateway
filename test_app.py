"""Unit tests for payment gateway tokenizer service."""
import pytest
import json
from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_tokenizer():
    """Sample tokenizer payload for testing."""
    return {"name": "test-card", "value": "4111111111111111"}


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check_returns_200(self, client):
        """Health endpoint should return 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_returns_up_status(self, client):
        """Health endpoint should return UP status."""
        response = client.get("/health")
        data = json.loads(response.data)
        assert data["status"] == "UP"
