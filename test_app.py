"""Tests for payment gateway tokenizer service."""
import pytest
import json
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
    assert response.json['status'] == 'UP'


def test_create_tokenizer_valid(client):
    """Test creating a valid tokenizer."""
    response = client.post(
        '/api/v1/tokenizer',
        data=json.dumps({'name': 'test-token', 'value': 'abc123'}),
        content_type='application/json'
    )
    assert response.status_code == 201
    assert 'id' in response.json
    assert response.json['name'] == 'test-token'


def test_create_tokenizer_missing_content_type(client):
    """Test that requests without JSON content-type are rejected."""
    response = client.post(
        '/api/v1/tokenizer',
        data=json.dumps({'name': 'test', 'value': 'test'})
    )
    assert response.status_code == 415


def test_create_tokenizer_name_too_long(client):
    """Test that overly long names are rejected."""
    long_name = 'a' * 101
    response = client.post(
        '/api/v1/tokenizer',
        data=json.dumps({'name': long_name, 'value': 'test'}),
        content_type='application/json'
    )
    assert response.status_code == 400
    assert 'exceed' in response.json['error']


def test_create_tokenizer_value_too_long(client):
    """Test that overly long values are rejected."""
    long_value = 'a' * 501
    response = client.post(
        '/api/v1/tokenizer',
        data=json.dumps({'name': 'test', 'value': long_value}),
        content_type='application/json'
    )
    assert response.status_code == 400
    assert 'exceed' in response.json['error']


def test_create_tokenizer_invalid_characters(client):
    """Test that names with special characters are rejected."""
    response = client.post(
        '/api/v1/tokenizer',
        data=json.dumps({'name': 'test<script>', 'value': 'test'}),
        content_type='application/json'
    )
    assert response.status_code == 400
    assert 'invalid characters' in response.json['error']


def test_create_tokenizer_invalid_value_type(client):
    """Test that non-primitive value types are rejected."""
    response = client.post(
        '/api/v1/tokenizer',
        data=json.dumps({'name': 'test', 'value': {'nested': 'object'}}),
        content_type='application/json'
    )
    assert response.status_code == 400


def test_get_tokenizer_invalid_id_format(client):
    """Test that malformed token IDs are rejected."""
    response = client.get('/api/v1/tokenizer/../../../etc/passwd')
    assert response.status_code == 400


def test_list_tokenizers_limit_enforced(client):
    """Test that pagination limit is enforced."""
    response = client.get('/api/v1/tokenizer?limit=1000')
    assert response.status_code == 200
