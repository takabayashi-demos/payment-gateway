"""Unit tests for payment gateway tokenizer service."""
import pytest
import json
from app import app, _tokenizers, _next_id


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
    # Clean up after each test
    _tokenizers.clear()


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


class TestListTokenizers:
    """Tests for listing tokenizers."""

    def test_list_empty_tokenizers(self, client):
        """List should return empty array when no tokenizers exist."""
        response = client.get("/api/v1/tokenizer")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_tokenizers_with_data(self, client, sample_tokenizer):
        """List should return tokenizers when they exist."""
        client.post("/api/v1/tokenizer", json=sample_tokenizer)
        response = client.get("/api/v1/tokenizer")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["items"][0]["name"] == "test-card"

    def test_list_tokenizers_pagination(self, client):
        """List should respect limit parameter."""
        for i in range(5):
            client.post("/api/v1/tokenizer", json={"name": f"card-{i}", "value": i})
        response = client.get("/api/v1/tokenizer?limit=3")
        data = json.loads(response.data)
        assert len(data["items"]) == 3
        assert data["total"] == 5


class TestGetTokenizer:
    """Tests for retrieving a single tokenizer."""

    def test_get_existing_tokenizer(self, client, sample_tokenizer):
        """Get should return tokenizer when it exists."""
        create_response = client.post("/api/v1/tokenizer", json=sample_tokenizer)
        token_id = json.loads(create_response.data)["id"]
        
        response = client.get(f"/api/v1/tokenizer/{token_id}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["id"] == token_id
        assert data["name"] == "test-card"
        assert data["value"] == "4111111111111111"

    def test_get_nonexistent_tokenizer(self, client):
        """Get should return 404 for non-existent tokenizer."""
        response = client.get("/api/v1/tokenizer/tok_999")
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data
        assert data["error"] == "Tokenizer not found"


class TestCreateTokenizer:
    """Tests for creating tokenizers."""

    def test_create_valid_tokenizer(self, client, sample_tokenizer):
        """Create should return 201 with valid payload."""
        response = client.post("/api/v1/tokenizer", json=sample_tokenizer)
        assert response.status_code == 201
        data = json.loads(response.data)
        assert "id" in data
        assert data["id"].startswith("tok_")
        assert data["name"] == "test-card"
        assert data["value"] == "4111111111111111"

    def test_create_tokenizer_missing_name(self, client):
        """Create should return 400 when name is missing."""
        response = client.post("/api/v1/tokenizer", json={"value": "123"})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "name and value are required" in data["error"]

    def test_create_tokenizer_missing_value(self, client):
        """Create should return 400 when value is missing."""
        response = client.post("/api/v1/tokenizer", json={"name": "test"})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_create_tokenizer_empty_payload(self, client):
        """Create should return 400 with empty payload."""
        response = client.post("/api/v1/tokenizer", json={})
        assert response.status_code == 400

    def test_create_tokenizer_no_json(self, client):
        """Create should return 400 with no JSON body."""
        response = client.post("/api/v1/tokenizer")
        assert response.status_code == 400

    def test_create_tokenizer_increments_id(self, client):
        """Create should generate sequential IDs."""
        response1 = client.post("/api/v1/tokenizer", json={"name": "a", "value": 1})
        response2 = client.post("/api/v1/tokenizer", json={"name": "b", "value": 2})
        
        id1 = json.loads(response1.data)["id"]
        id2 = json.loads(response2.data)["id"]
        
        assert id1 == "tok_1"
        assert id2 == "tok_2"

    def test_create_tokenizer_with_zero_value(self, client):
        """Create should accept 0 as a valid value."""
        response = client.post("/api/v1/tokenizer", json={"name": "zero", "value": 0})
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["value"] == 0
