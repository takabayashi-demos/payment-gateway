"""Tests for payment gateway tokenizer service."""
import pytest
import threading
from app import app


@pytest.fixture
def client():
    """Create test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "UP"


def test_create_tokenizer(client):
    """Test creating a tokenizer."""
    response = client.post(
        "/api/v1/tokenizer",
        json={"name": "test_token", "value": "abc123"}
    )
    assert response.status_code == 201
    assert response.json["name"] == "test_token"
    assert response.json["value"] == "abc123"
    assert "id" in response.json


def test_create_tokenizer_missing_fields(client):
    """Test validation for missing required fields."""
    response = client.post("/api/v1/tokenizer", json={"name": "test"})
    assert response.status_code == 400
    
    response = client.post("/api/v1/tokenizer", json={"value": "test"})
    assert response.status_code == 400


def test_get_tokenizer(client):
    """Test retrieving a tokenizer."""
    create_response = client.post(
        "/api/v1/tokenizer",
        json={"name": "test_token", "value": "abc123"}
    )
    token_id = create_response.json["id"]
    
    response = client.get(f"/api/v1/tokenizer/{token_id}")
    assert response.status_code == 200
    assert response.json["id"] == token_id


def test_get_nonexistent_tokenizer(client):
    """Test retrieving a tokenizer that doesn't exist."""
    response = client.get("/api/v1/tokenizer/tok_999999")
    assert response.status_code == 404


def test_list_tokenizers(client):
    """Test listing tokenizers."""
    # Create a few tokenizers
    for i in range(3):
        client.post(
            "/api/v1/tokenizer",
            json={"name": f"token_{i}", "value": f"value_{i}"}
        )
    
    response = client.get("/api/v1/tokenizer")
    assert response.status_code == 200
    assert len(response.json["items"]) >= 3


def test_concurrent_tokenizer_creation(client):
    """Test that concurrent requests generate unique IDs."""
    results = []
    errors = []
    
    def create_tokenizer(index):
        try:
            response = client.post(
                "/api/v1/tokenizer",
                json={"name": f"token_{index}", "value": f"value_{index}"}
            )
            results.append(response.json)
        except Exception as e:
            errors.append(e)
    
    # Create 20 tokenizers concurrently
    threads = []
    for i in range(20):
        thread = threading.Thread(target=create_tokenizer, args=(i,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(results) == 20
    
    # Check all IDs are unique
    ids = [r["id"] for r in results]
    assert len(ids) == len(set(ids)), "Duplicate IDs detected"
