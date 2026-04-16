"""Pytest fixtures for payment-gateway tests."""
import pytest
import app as app_module


@pytest.fixture
def client():
    """Create a Flask test client."""
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        app_module._tokenizers.clear()
        app_module._next_id = 1
        yield c
