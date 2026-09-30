import time
import unittest
from unittest.mock import patch

from ratelimiter.limiter import RateLimitExceeded, SlidingWindow, TokenBucket


class TestTokenBucket(unittest.TestCase):
    def test_allows_up_to_capacity(self):
        bucket = TokenBucket(capacity=3, rate=1.0)
        for _ in range(3):
            self.assertTrue(bucket.try_consume())

    def test_blocks_when_empty(self):
        bucket = TokenBucket(capacity=2, rate=0.1)
        bucket.try_consume()
        bucket.try_consume()
        self.assertFalse(bucket.try_consume())

    def test_consume_raises_rate_limit_exceeded(self):
        bucket = TokenBucket(capacity=1, rate=0.1)
        bucket.consume()
        with self.assertRaises(RateLimitExceeded) as ctx:
            bucket.consume()
        self.assertGreater(ctx.exception.retry_after, 0)

    def test_tokens_refill_over_time(self):
        bucket = TokenBucket(capacity=2, rate=10.0)
        bucket.try_consume()
        bucket.try_consume()
        time.sleep(0.15)  # ~1.5 tokens at rate=10
        self.assertTrue(bucket.try_consume())

    def test_invalid_params_raise(self):
        with self.assertRaises(ValueError):
            TokenBucket(capacity=0, rate=1.0)
        with self.assertRaises(ValueError):
            TokenBucket(capacity=1, rate=-1.0)

    def test_available_tokens_decreases(self):
        bucket = TokenBucket(capacity=5, rate=1.0)
        before = bucket.available_tokens
        bucket.try_consume()
        self.assertLess(bucket.available_tokens, before)


class TestSlidingWindow(unittest.TestCase):
    def test_allows_up_to_max_calls(self):
        w = SlidingWindow(max_calls=3, window_seconds=10.0)
        for _ in range(3):
            self.assertTrue(w.try_consume())

    def test_blocks_when_window_full(self):
        w = SlidingWindow(max_calls=2, window_seconds=10.0)
        w.try_consume()
        w.try_consume()
        self.assertFalse(w.try_consume())

    def test_consume_raises_with_retry_after(self):
        w = SlidingWindow(max_calls=1, window_seconds=5.0)
        w.consume()
        with self.assertRaises(RateLimitExceeded) as ctx:
            w.consume()
        self.assertGreater(ctx.exception.retry_after, 0)

    def test_window_slides(self):
        w = SlidingWindow(max_calls=2, window_seconds=0.2)
        w.try_consume()
        w.try_consume()
        self.assertFalse(w.try_consume())
        time.sleep(0.25)
        self.assertTrue(w.try_consume())

    def test_remaining_calls(self):
        w = SlidingWindow(max_calls=5, window_seconds=10.0)
        self.assertEqual(w.remaining_calls, 5)
        w.try_consume()
        w.try_consume()
        self.assertEqual(w.remaining_calls, 3)

    def test_invalid_params_raise(self):
        with self.assertRaises(ValueError):
            SlidingWindow(max_calls=0, window_seconds=1.0)


if __name__ == "__main__":
    unittest.main()
