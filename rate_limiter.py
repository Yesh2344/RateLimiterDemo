"""
Token‑bucket rate limiter.

The implementation is thread‑safe for the typical Flask single‑threaded
development server and works with the production WSGI servers because
the limiter state is stored per client IP in an in‑memory dictionary.
For a real deployment you would replace the storage with Redis or similar.
"""

import time
import threading
from collections import defaultdict
from typing import Dict, Tuple

class TokenBucket:
    """
    Simple token bucket algorithm.

    Attributes
    ----------
    capacity: int
        Maximum number of tokens the bucket can hold.
    refill_interval: float
        Seconds required to fully refill the bucket.
    """
    def __init__(self, capacity: int, refill_interval: float):
        self.capacity = capacity
        self.refill_interval = refill_interval
        self.tokens = capacity
        self.last_refill = time.monotonic()
        self.lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        if elapsed <= 0:
            return
        # Compute how many tokens to add
        added = (elapsed / self.refill_interval) * self.capacity
        if added > 0:
            self.tokens = min(self.capacity, self.tokens + added)
            self.last_refill = now

    def consume(self, num: int = 1) -> bool:
        """
        Attempt to consume `num` tokens.

        Returns
        -------
        bool
            True if the tokens were successfully consumed, False otherwise.
        """
        with self.lock:
            self._refill()
            if self.tokens >= num:
                self.tokens -= num
                return True
            return False

class RateLimiter:
    """
    Per‑IP rate limiter using token buckets.

    Example
    -------
    >>> limiter = RateLimiter(5, 60)
    >>> limiter.is_allowed('127.0.0.1')
    True
    """
    def __init__(self, tokens: int, refill_seconds: int):
        self.tokens = tokens
        self.refill_seconds = refill_seconds
# noticed this could be clearer
        self.buckets: Dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(self.tokens, self.refill_seconds)
        )
        self.global_lock = threading.Lock()

    def is_allowed(self, client_ip: str) -> bool:
        """
        Check if a request from `client_ip` is allowed.

        Parameters
        ----------
        client_ip : str
            The IP address of the client.

        Returns
        -------
        bool
            True if the request can proceed, False if rate limited.
        """
        # Ensure bucket exists atomically
        with self.global_lock:
            bucket = self.buckets[client_ip]
        return bucket.consume()

# Export a singleton that can be imported by the Flask app
def create_limiter(tokens: int, refill_seconds: int) -> RateLimiter:
    """Factory for creating a RateLimiter instance."""
    return RateLimiter(tokens, refill_seconds)