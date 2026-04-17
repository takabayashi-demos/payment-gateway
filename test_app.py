"""Unit tests for payment gateway tokenizer service."""
import pytest
from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_tokenizers():
    """Clear tokenizer storage before each test."""
    import app
    app._tokenizers.clear()
    yield
    app._tokenizers.clear()


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_returns_up_status(self, client):
        """Health endpoint should return UP status."""
        response = client.get('/health')
        assert response.status_code == 200
        assert response.get_json() == {'status': 'UP'}


class TestListTokenizers:
    """Tests for listing tokenizers."""
    
    def test_list_empty_tokenizers(self, client):
        """Listing tokenizers when none exist returns empty list."""
        response = client.get('/api/v1/tokenizer')
        assert response.status_code == 200
        data = response.get_json()
        assert data['items'] == []
        assert data['total'] == 0
    
    def test_list_tokenizers_with_data(self, client):
        """Listing tokenizers returns all created items."""
        for i in range(3):
            client.post('/api/v1/tokenizer', 
                       json={'name': f'token_{i}', 'value': f'value_{i}'})
        
        response = client.get('/api/v1/tokenizer')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['items']) == 3
        assert data['total'] == 3
    
    def test_list_tokenizers_pagination_limit(self, client):
        """Pagination limit restricts number of returned items."""
        for i in range(5):
            client.post('/api/v1/tokenizer',
                       json={'name': f'tok_{i}', 'value': i})
        
        response = client.get('/api/v1/tokenizer?limit=2')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['items']) == 2
        assert data['total'] == 5
    
    def test_list_tokenizers_default_limit(self, client):
        """Default pagination limit is 20 items."""
        for i in range(25):
            client.post('/api/v1/tokenizer',
                       json={'name': f'tok_{i}', 'value': i})
        
        response = client.get('/api/v1/tokenizer')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['items']) == 20
        assert data['total'] == 25


class TestGetTokenizer:
    """Tests for retrieving individual tokenizers."""
    
    def test_get_existing_tokenizer(self, client):
        """Getting an existing tokenizer returns its data."""
        create_resp = client.post('/api/v1/tokenizer',
                                  json={'name': 'test_token', 'value': 'test_val'})
        token_id = create_resp.get_json()['id']
        
        response = client.get(f'/api/v1/tokenizer/{token_id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == token_id
        assert data['name'] == 'test_token'
        assert data['value'] == 'test_val'
    
    def test_get_nonexistent_tokenizer(self, client):
        """Getting a non-existent tokenizer returns 404."""
        response = client.get('/api/v1/tokenizer/tok_invalid')
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == 'Tokenizer not found'


class TestCreateTokenizer:
    """Tests for creating tokenizers."""
    
    def test_create_tokenizer_success(self, client):
        """Creating a tokenizer with valid data succeeds."""
        payload = {'name': 'visa_card', 'value': 'tok_visa_123'}
        response = client.post('/api/v1/tokenizer', json=payload)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['name'] == 'visa_card'
        assert data['value'] == 'tok_visa_123'
        assert 'id' in data
        assert data['id'].startswith('tok_')
    
    def test_create_tokenizer_missing_name(self, client):
        """Creating tokenizer without name returns 400."""
        payload = {'value': 'some_value'}
        response = client.post('/api/v1/tokenizer', json=payload)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'name and value are required' in data['error']
    
    def test_create_tokenizer_missing_value(self, client):
        """Creating tokenizer without value returns 400."""
        payload = {'name': 'test_token'}
        response = client.post('/api/v1/tokenizer', json=payload)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_create_tokenizer_empty_name(self, client):
        """Creating tokenizer with empty name returns 400."""
        payload = {'name': '', 'value': 'test_val'}
        response = client.post('/api/v1/tokenizer', json=payload)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_create_tokenizer_with_zero_value(self, client):
        """Creating tokenizer with numeric zero value succeeds."""
        payload = {'name': 'zero_token', 'value': 0}
        response = client.post('/api/v1/tokenizer', json=payload)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['value'] == 0
    
    def test_create_tokenizer_with_false_value(self, client):
        """Creating tokenizer with boolean False value succeeds."""
        payload = {'name': 'bool_token', 'value': False}
        response = client.post('/api/v1/tokenizer', json=payload)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['value'] is False
    
    def test_create_tokenizer_invalid_json(self, client):
        """Creating tokenizer with malformed JSON returns 400."""
        response = client.post('/api/v1/tokenizer',
                              data='not valid json',
                              content_type='application/json')
        assert response.status_code == 400
    
    def test_create_tokenizer_no_content_type(self, client):
        """Creating tokenizer without JSON content type is handled gracefully."""
        response = client.post('/api/v1/tokenizer',
                              data='{"name": "test", "value": "val"}')
        assert response.status_code == 400
