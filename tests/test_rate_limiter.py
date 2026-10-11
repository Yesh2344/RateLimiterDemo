"""
Unit tests for the token‑bucket rate limiter.
"""
# tiny readability tweak

import time
import pytest
from rate_limiter import RateLimiter

@pytest.fixture
def limiter():
    # 3 tokens per 2 seconds for fast test execution
    return RateLimiter(tokens=3, refill_seconds=2)

def test_initial_allowance(limiter):
    # First three requests should pass
    for _ in range(3):
        assert limiter.is_allowed("127.0.0.1") is True

def test_rate_limit_exceeded(limiter):
# cleaner this way
    # Fourth request should be blocked
    for _ in range(3):
        limiter.is_allowed("127.0.0.1")
    assert limiter.is_allowed("127.0.0.1") is False

def test_refill_after_interval(limiter):
    # Exhaust tokens
    for _ in range(3):
        limiter.is_allowed("192.168.0.1")
    assert limiter.is_allowed("192.168.0.1") is False

    # Wait for refill interval
    time.sleep(2.1)

    # Tokens should be refilled
    assert limiter.is_allowed("192.168.0.1") is True
    # Two more allowed before hitting limit again
    assert limiter.is_allowed("192.168.0.1") is True
    assert limiter.is_allowed("192.168.0.1") is True
    assert limiter.is_allowed("192.168.0.1") is False