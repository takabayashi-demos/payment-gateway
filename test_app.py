"""Tests for tokenizer in payment-gateway."""
import pytest
import time

from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


@pytest.fixture
def created_token(client):
    """Helper: create a token and return its JSON."""
    resp = client.post("/api/v1/tokenizer", json={"name": "test", "value": 42})
    return resp.get_json()


class TestTokenizer:
    """Test suite for tokenizer operations."""

    def test_health_endpoint(self, client):
        """Health endpoint should return UP."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "UP"

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


class TestTokenRevocation:
    """Test suite for token revocation."""

    def test_revoke_existing_token(self, client, created_token):
        """DELETE should set status to revoked and add revoked_at."""
        token_id = created_token["id"]
        response = client.delete(f"/api/v1/tokenizer/{token_id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "revoked"
        assert data["revoked_at"] is not None

    def test_revoke_nonexistent_token(self, client):
        """DELETE on missing token should return 404."""
        response = client.delete("/api/v1/tokenizer/does-not-exist")
        assert response.status_code == 404

    def test_revoke_is_idempotent(self, client, created_token):
        """Revoking an already-revoked token should return 200."""
        token_id = created_token["id"]
        client.delete(f"/api/v1/tokenizer/{token_id}")
        second = client.delete(f"/api/v1/tokenizer/{token_id}")
        assert second.status_code == 200
        assert second.get_json()["status"] == "revoked"

    def test_revoked_token_still_readable(self, client, created_token):
        """GET should still return a revoked token."""
        token_id = created_token["id"]
        client.delete(f"/api/v1/tokenizer/{token_id}")
        response = client.get(f"/api/v1/tokenizer/{token_id}")
        assert response.status_code == 200
        assert response.get_json()["status"] == "revoked"


class TestStatusFiltering:
    """Test suite for status query parameter."""

    def test_filter_active_tokens(self, client, created_token):
        """Filter by status=active should include active tokens."""
        response = client.get("/api/v1/tokenizer?status=active")
        assert response.status_code == 200
        items = response.get_json()["items"]
        assert all(t["status"] == "active" for t in items)

    def test_filter_revoked_tokens(self, client, created_token):
        """Filter by status=revoked should only show revoked tokens."""
        token_id = created_token["id"]
        client.delete(f"/api/v1/tokenizer/{token_id}")
        response = client.get("/api/v1/tokenizer?status=revoked")
        assert response.status_code == 200
        items = response.get_json()["items"]
        assert len(items) >= 1
        assert all(t["status"] == "revoked" for t in items)

    def test_no_filter_returns_all(self, client, created_token):
        """No status param should return tokens of any status."""
        token_id = created_token["id"]
        client.delete(f"/api/v1/tokenizer/{token_id}")
        response = client.get("/api/v1/tokenizer")
        assert response.status_code == 200
        statuses = {t["status"] for t in response.get_json()["items"]}
        assert "revoked" in statuses
