"""Tests for webhook in payment-gateway."""
import pytest
import time


class TestWebhook:
    """Test suite for webhook operations."""

    def test_health_endpoint(self, client):
        """Health endpoint should return UP."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "UP"

    def test_webhook_create(self, client):
        """Should create a new webhook entry."""
        payload = {"name": "test", "value": 42}
        response = client.post("/api/v1/webhook", json=payload)
        assert response.status_code in (200, 201)

    def test_webhook_validation(self, client):
        """Should reject invalid webhook data."""
        response = client.post("/api/v1/webhook", json={})
        assert response.status_code in (400, 422)

    def test_webhook_not_found(self, client):
        """Should return 404 for missing webhook."""
        response = client.get("/api/v1/webhook/nonexistent")
        assert response.status_code == 404

    @pytest.mark.parametrize("limit", [1, 10, 50, 100])
    def test_webhook_pagination(self, client, limit):
        """Should respect pagination limits."""
        response = client.get(f"/api/v1/webhook?limit={limit}")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data.get("items", data.get("webhooks", []))) <= limit

    def test_webhook_performance(self, client):
        """Response time should be under 500ms."""
        start = time.monotonic()
        response = client.get("/api/v1/webhook")
        elapsed = time.monotonic() - start
        assert elapsed < 0.5, f"Took {elapsed:.2f}s, expected <0.5s"
