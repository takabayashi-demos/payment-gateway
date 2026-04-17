"""Unit tests for payment gateway tokenizer service."""
import json
import pytest
from app import app


@pytest.fixture
def client():
    """Create a test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_check(client):
    """Test health endpoint returns UP status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "UP"


def test_list_tokenizers_empty(client):
    """Test listing tokenizers when none exist."""
    response = client.get("/api/v1/tokenizer")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["items"] == []
    assert data["total"] == 0


def test_create_tokenizer_success(client):
    """Test creating a new tokenizer with valid data."""
    payload = {"name": "visa_test", "value": "4111111111111111"}
    response = client.post(
        "/api/v1/tokenizer",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data["name"] == "visa_test"
    assert data["value"] == "4111111111111111"
    assert "tok_" in data["id"]


def test_create_tokenizer_missing_name(client):
    """Test creating tokenizer without required name field."""
    payload = {"value": "test_value"}
    response = client.post(
        "/api/v1/tokenizer",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


def test_create_tokenizer_missing_value(client):
    """Test creating tokenizer without required value field."""
    payload = {"name": "test_name"}
    response = client.post(
        "/api/v1/tokenizer",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


def test_get_tokenizer_success(client):
    """Test retrieving an existing tokenizer."""
    payload = {"name": "mastercard_test", "value": "5500000000000004"}
    create_response = client.post(
        "/api/v1/tokenizer",
        data=json.dumps(payload),
        content_type="application/json",
    )
    created = json.loads(create_response.data)
    token_id = created["id"]

    response = client.get(f"/api/v1/tokenizer/{token_id}")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["id"] == token_id
    assert data["name"] == "mastercard_test"
    assert data["value"] == "5500000000000004"


def test_get_tokenizer_not_found(client):
    """Test retrieving a non-existent tokenizer."""
    response = client.get("/api/v1/tokenizer/tok_nonexistent")
    assert response.status_code == 404
    data = json.loads(response.data)
    assert "error" in data
    assert "not found" in data["error"].lower()


def test_list_tokenizers_pagination(client):
    """Test tokenizer list pagination."""
    for i in range(5):
        payload = {"name": f"token_{i}", "value": f"value_{i}"}
        client.post(
            "/api/v1/tokenizer",
            data=json.dumps(payload),
            content_type="application/json",
        )

    response = client.get("/api/v1/tokenizer?limit=3")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data["items"]) == 3
    assert data["total"] == 5


def test_create_tokenizer_incremental_ids(client):
    """Test that tokenizer IDs increment correctly."""
    payload1 = {"name": "first", "value": "val1"}
    payload2 = {"name": "second", "value": "val2"}

    resp1 = client.post(
        "/api/v1/tokenizer",
        data=json.dumps(payload1),
        content_type="application/json",
    )
    resp2 = client.post(
        "/api/v1/tokenizer",
        data=json.dumps(payload2),
        content_type="application/json",
    )

    data1 = json.loads(resp1.data)
    data2 = json.loads(resp2.data)

    assert data1["id"] == "tok_1"
    assert data2["id"] == "tok_2"
