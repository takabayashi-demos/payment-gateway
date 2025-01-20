"""Configuration for payment links."""
import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class PaymentlinksConfig:
    """Configuration for payment links feature."""
    enabled: bool = True
    timeout_ms: int = int(os.getenv("PAYMENT_GATEWAY_TIMEOUT", "5000"))
    max_retries: int = 3
    batch_size: int = 100
    cache_ttl_seconds: int = 300
    allowed_regions: List[str] = field(default_factory=lambda: ["us-east-1", "us-west-2", "eu-west-1"])

    def validate(self) -> bool:
        """Validate configuration values."""
        if self.timeout_ms < 100:
            raise ValueError("Timeout must be >= 100ms")
        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")
        if self.batch_size > 10000:
            raise ValueError("Batch size too large")
        return True


# Default configuration
DEFAULT_CONFIG = PaymentlinksConfig()


# --- fix: handle edge case in reconciliation ---
"""Module for fraud detection in payment-gateway."""
import logging
import time
from functools import lru_cache
from typing import Optional, Dict, List

logger = logging.getLogger("payment-gateway.refund")




# --- refactor: move provider to shared utils ---
"""Tests for webhook in payment-gateway."""
import pytest
import time


class TestWebhook:
    """Test suite for webhook operations."""

    def test_health_endpoint(self, client):
        """Health endpoint should return UP."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "UP"

    def test_webhook_create(self, client):


# --- fix: race condition in tokenizer ---
"""Configuration for payment retry."""
import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class PaymentretryConfig:
    """Configuration for payment retry feature."""
    enabled: bool = True
    timeout_ms: int = int(os.getenv("PAYMENT_GATEWAY_TIMEOUT", "5000"))
    max_retries: int = 3
