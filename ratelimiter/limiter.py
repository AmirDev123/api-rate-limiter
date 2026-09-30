"""
Rate limiting algorithms.

TokenBucket  — allow bursts up to `capacity`, refilled at `rate` tokens/sec.
SlidingWindow — allow at most `max_calls` requests in a rolling `window_seconds` window.
"""
import threading
import time
from collections import deque


class RateLimitExceeded(Exception):
    """Raised when a rate limit is exceeded."""
    def __init__(self, retry_after: float = 0.0):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after:.2f}s")


class TokenBucket:
    """
    Classic token-bucket rate limiter.

    capacity   — maximum burst size (tokens)
    rate       — refill rate in tokens per second
    """
    def __init__(self, capacity: float, rate: float):
        if capacity <= 0 or rate <= 0:
            raise ValueError("capacity and rate must be positive")
        self.capacity = capacity
        self.rate = rate
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last_refill = now

    def consume(self, tokens: float = 1.0) -> None:
        """Consume `tokens` from the bucket. Raises RateLimitExceeded if not enough."""
        with self._lock:
            self._refill()
            if self._tokens < tokens:
                wait = (tokens - self._tokens) / self.rate
                raise RateLimitExceeded(retry_after=wait)
            self._tokens -= tokens

    def try_consume(self, tokens: float = 1.0) -> bool:
        """Return True if tokens were consumed, False if rate limited."""
        try:
            self.consume(tokens)
            return True
        except RateLimitExceeded:
            return False

    @property
    def available_tokens(self) -> float:
        with self._lock:
            self._refill()
            return round(self._tokens, 4)


class SlidingWindow:
    """
    Sliding-window rate limiter.

    max_calls      — maximum allowed calls in the window
    window_seconds — size of the rolling time window
    """
    def __init__(self, max_calls: int, window_seconds: float):
        if max_calls <= 0 or window_seconds <= 0:
            raise ValueError("max_calls and window_seconds must be positive")
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._timestamps: deque[float] = deque()
        self._lock = threading.Lock()

    def _evict_old(self, now: float) -> None:
        cutoff = now - self.window_seconds
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

    def consume(self) -> None:
        """Record a call. Raises RateLimitExceeded if the window is full."""
        with self._lock:
            now = time.monotonic()
            self._evict_old(now)
            if len(self._timestamps) >= self.max_calls:
                oldest = self._timestamps[0]
                retry_after = self.window_seconds - (now - oldest)
                raise RateLimitExceeded(retry_after=max(0.0, retry_after))
            self._timestamps.append(now)

    def try_consume(self) -> bool:
        """Return True if the call was allowed, False if rate limited."""
        try:
            self.consume()
            return True
        except RateLimitExceeded:
            return False

    @property
    def remaining_calls(self) -> int:
        with self._lock:
            self._evict_old(time.monotonic())
            return max(0, self.max_calls - len(self._timestamps))
