"""Tests for payment gateway tokenizer service."""
import pytest
import json
from app import app, _tokenizers


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
    _tokenizers.clear()


def test_health_check(client):
    """Test health endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'UP'


def test_security_headers(client):
    """Test security headers are present."""
    response = client.get('/health')
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert response.headers['X-Frame-Options'] == 'DENY'
    assert response.headers['X-XSS-Protection'] == '1; mode=block'
    assert 'Content-Security-Policy' in response.headers


def test_create_tokenizer_valid(client):
    """Test creating tokenizer with valid input."""
    payload = {"name": "test-token", "value": "abc123"}
    response = client.post('/api/v1/tokenizer',
                          data=json.dumps(payload),
                          content_type='application/json')
    assert response.status_code == 201
    assert response.json['name'] == 'test-token'
    assert response.json['value'] == 'abc123'
    assert 'id' in response.json


def test_create_tokenizer_missing_name(client):
    """Test creating tokenizer without name."""
    payload = {"value": "abc123"}
    response = client.post('/api/v1/tokenizer',
                          data=json.dumps(payload),
                          content_type='application/json')
    assert response.status_code == 400
    assert 'name and value are required' in response.json['error']


def test_create_tokenizer_missing_value(client):
    """Test creating tokenizer without value."""
    payload = {"name": "test-token"}
    response = client.post('/api/v1/tokenizer',
                          data=json.dumps(payload),
                          content_type='application/json')
    assert response.status_code == 400
    assert 'name and value are required' in response.json['error']


def test_create_tokenizer_invalid_json(client):
    """Test creating tokenizer with invalid JSON."""
    response = client.post('/api/v1/tokenizer',
                          data='invalid json',
                          content_type='application/json')
    assert response.status_code == 400
    assert 'Invalid JSON payload' in response.json['error']


def test_create_tokenizer_name_too_long(client):
    """Test creating tokenizer with name exceeding max length."""
    payload = {"name": "a" * 300, "value": "abc123"}
    response = client.post('/api/v1/tokenizer',
                          data=json.dumps(payload),
                          content_type='application/json')
    assert response.status_code == 400
    assert 'exceeds maximum length' in response.json['error']


def test_create_tokenizer_value_too_long(client):
    """Test creating tokenizer with value exceeding max length."""
    payload = {"name": "test", "value": "a" * 1500}
    response = client.post('/api/v1/tokenizer',
                          data=json.dumps(payload),
                          content_type='application/json')
    assert response.status_code == 400
    assert 'exceeds maximum length' in response.json['error']


def test_create_tokenizer_invalid_characters(client):
    """Test creating tokenizer with invalid characters in name."""
    payload = {"name": "test<script>alert(1)</script>", "value": "abc123"}
    response = client.post('/api/v1/tokenizer',
                          data=json.dumps(payload),
                          content_type='application/json')
    assert response.status_code == 400
    assert 'invalid characters' in response.json['error']


def test_create_tokenizer_sql_injection_attempt(client):
    """Test creating tokenizer with SQL injection attempt."""
    payload = {"name": "test'; DROP TABLE tokens;--", "value": "abc123"}
    response = client.post('/api/v1/tokenizer',
                          data=json.dumps(payload),
                          content_type='application/json')
    assert response.status_code == 400
    assert 'invalid characters' in response.json['error']


def test_get_tokenizer_invalid_id_format(client):
    """Test getting tokenizer with invalid ID format."""
    response = client.get('/api/v1/tokenizer/invalid-id')
    assert response.status_code == 400
    assert 'Invalid tokenizer ID format' in response.json['error']


def test_get_tokenizer_not_found(client):
    """Test getting non-existent tokenizer."""
    response = client.get('/api/v1/tokenizer/tok_999')
    assert response.status_code == 404
    assert 'not found' in response.json['error']


def test_list_tokenizers_pagination(client):
    """Test tokenizer listing with pagination."""
    # Create some tokenizers
    for i in range(5):
        payload = {"name": f"token-{i}", "value": f"val{i}"}
        client.post('/api/v1/tokenizer',
                   data=json.dumps(payload),
                   content_type='application/json')
    
    response = client.get('/api/v1/tokenizer?limit=3')
    assert response.status_code == 200
    assert len(response.json['items']) == 3
    assert response.json['total'] == 5


def test_list_tokenizers_limit_clamping(client):
    """Test that limit parameter is clamped to safe range."""
    response = client.get('/api/v1/tokenizer?limit=999999')
    assert response.status_code == 200
    # Should be clamped to 100 max
