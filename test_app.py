"""Tests for tokenizer in payment-gateway."""
import pytest
import time


class TestTokenizer:
    """Test suite for tokenizer operations."""

    def test_health_endpoint(self, client):
        """Health endpoint should return UP with pool info."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "UP"
        assert "pool_size" in data

    def test_tokenizer_create(self, client):
        """Should create a new tokenizer entry."""
        payload = {"name": "test", "value": 42}
        response = client.post("/api/v1/tokenizer", json=payload)
        assert response.status_code in (200, 201)

    def test_tokenizer_validation(self, client):
        """Should reject invalid tokenizer data."""
        response = client.post("/api/v1/tokenizer", json={})
        assert response.status_code in (400, 422)

    def test_tokenizer_not_found(self, client):
        """Should return 404 for missing tokenizer."""
        response = client.get("/api/v1/tokenizer/nonexistent")
        assert response.status_code == 404

    @pytest.mark.parametrize("limit", [1, 10, 50, 100])
    def test_tokenizer_pagination(self, client, limit):
        """Should respect pagination limits."""
        response = client.get(f"/api/v1/tokenizer?limit={limit}")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data.get("items", data.get("tokenizers", []))) <= limit

    def test_tokenizer_performance(self, client):
        """Response time should be under 500ms."""
        start = time.monotonic()
        response = client.get("/api/v1/tokenizer")
        elapsed = time.monotonic() - start
        assert elapsed < 0.5, f"Took {elapsed:.2f}s, expected <0.5s"

    def test_cached_read_after_create(self, client):
        """Creating a tokenizer should invalidate cache so subsequent reads are fresh."""
        client.get("/api/v1/tokenizer")
        client.post("/api/v1/tokenizer", json={"name": "cached", "value": 99})
        response = client.get("/api/v1/tokenizer")
        assert response.status_code == 200
        items = response.get_json()["items"]
        assert any(t["name"] == "cached" for t in items)

    def test_repeat_read_uses_cache(self, client):
        """Second identical GET should be served from cache (faster)."""
        client.get("/api/v1/tokenizer")
        start = time.monotonic()
        response = client.get("/api/v1/tokenizer")
        elapsed = time.monotonic() - start
        assert response.status_code == 200
        assert elapsed < 0.1, f"Cached read took {elapsed:.3f}s, expected <0.1s"
