"""Shared fixtures for payment-gateway tests."""
import json
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

import app as app_module


@pytest.fixture(autouse=True)
def _mock_redis():
    """Replace Redis with a simple dict-backed mock."""
    store = {}

    class FakeRedis:
        def get(self, key):
            entry = store.get(key)
            if entry is None:
                return None
            return entry["data"]

        def setex(self, key, ttl, data):
            store[key] = {"data": data, "ttl": ttl}

        def delete(self, *keys):
            for k in keys:
                store.pop(k, None)

        def scan(self, cursor, match=None, count=100):
            matched = [k for k in store if k.startswith(match.replace("*", ""))]
            return (0, matched)

    fake = FakeRedis()
    with patch.object(app_module, "_get_redis", return_value=fake):
        yield fake


@pytest.fixture()
def client():
    """Create a test client with an in-memory SQLite database."""
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with test_engine.connect() as conn:
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS tokenizers ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "name TEXT NOT NULL, "
            "value INTEGER NOT NULL, "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        ))
        conn.commit()

    app_module.engine = test_engine
    app_module.app.config["TESTING"] = True

    with app_module.app.test_client() as c:
        yield c
