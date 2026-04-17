"""Tests for payment gateway service."""
import pytest
from app import app


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health(client):
    """Test health endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {"status": "UP"}


def test_list_tokenizers_with_negative_limit(client):
    """Test that negative limit returns error."""
    response = client.get('/api/v1/tokenizer?limit=-5')
    assert response.status_code == 400
    assert "positive" in response.json.get("error", "").lower()


def test_list_tokenizers_with_zero_limit(client):
    """Test that zero limit returns error."""
    response = client.get('/api/v1/tokenizer?limit=0')
    assert response.status_code == 400


def test_list_tokenizers_with_large_limit(client):
    """Test that excessively large limit is capped."""
    for i in range(10):
        client.post('/api/v1/tokenizer', json={"name": f"test{i}", "value": i})
    
    response = client.get('/api/v1/tokenizer?limit=9999')
    assert response.status_code == 200
    assert len(response.json["items"]) <= 100


def test_list_tokenizers_default(client):
    """Test default limit behavior."""
    response = client.get('/api/v1/tokenizer')
    assert response.status_code == 200
    assert "items" in response.json


def test_create_tokenizer(client):
    """Test creating a tokenizer."""
    response = client.post('/api/v1/tokenizer', json={"name": "test", "value": 42})
    assert response.status_code == 201
    assert response.json["name"] == "test"
    assert response.json["value"] == 42
    assert "id" in response.json


def test_create_tokenizer_missing_fields(client):
    """Test that missing fields return error."""
    response = client.post('/api/v1/tokenizer', json={"name": "test"})
    assert response.status_code == 400


def test_get_tokenizer(client):
    """Test getting a tokenizer by ID."""
    create_resp = client.post('/api/v1/tokenizer', json={"name": "test", "value": 42})
    token_id = create_resp.json["id"]
    
    response = client.get(f'/api/v1/tokenizer/{token_id}')
    assert response.status_code == 200
    assert response.json["id"] == token_id


def test_get_tokenizer_not_found(client):
    """Test getting non-existent tokenizer."""
    response = client.get('/api/v1/tokenizer/invalid')
    assert response.status_code == 404
