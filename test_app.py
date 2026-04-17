"""Tests for payment gateway tokenizer service."""
import concurrent.futures
import pytest
from app import app


@pytest.fixture
def client():
    """Create test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_check(client):
    """Test health endpoint returns UP."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "UP"


def test_create_tokenizer(client):
    """Test creating a single tokenizer."""
    response = client.post(
        "/api/v1/tokenizer",
        json={"name": "test_card", "value": "4111111111111111"},
    )
    assert response.status_code == 201
    data = response.json
    assert data["name"] == "test_card"
    assert data["value"] == "4111111111111111"
    assert data["id"].startswith("tok_")


def test_create_tokenizer_missing_fields(client):
    """Test validation for required fields."""
    response = client.post("/api/v1/tokenizer", json={"name": "test"})
    assert response.status_code == 400
    assert "error" in response.json


def test_get_tokenizer(client):
    """Test retrieving a tokenizer by ID."""
    create_response = client.post(
        "/api/v1/tokenizer",
        json={"name": "visa", "value": "4242424242424242"},
    )
    token_id = create_response.json["id"]

    response = client.get(f"/api/v1/tokenizer/{token_id}")
    assert response.status_code == 200
    assert response.json["id"] == token_id


def test_get_nonexistent_tokenizer(client):
    """Test 404 for nonexistent tokenizer."""
    response = client.get("/api/v1/tokenizer/tok_999999")
    assert response.status_code == 404


def test_list_tokenizers(client):
    """Test listing tokenizers with pagination."""
    for i in range(5):
        client.post(
            "/api/v1/tokenizer",
            json={"name": f"card_{i}", "value": f"411111111111{i:04d}"},
        )

    response = client.get("/api/v1/tokenizer?limit=3")
    assert response.status_code == 200
    assert len(response.json["items"]) == 3
    assert response.json["total"] >= 5


def test_concurrent_token_creation(client):
    """Test that concurrent requests generate unique token IDs."""
    def create_token(index):
        return client.post(
            "/api/v1/tokenizer",
            json={"name": f"card_{index}", "value": f"4111{index:012d}"},
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(create_token, i) for i in range(50)]
        responses = [f.result() for f in concurrent.futures.as_completed(futures)]

    token_ids = [r.json["id"] for r in responses]
    assert len(token_ids) == 50
    assert len(set(token_ids)) == 50, "Duplicate token IDs detected"
