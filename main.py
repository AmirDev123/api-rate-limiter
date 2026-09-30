#!/usr/bin/env python3
"""
Demo: api-rate-limiter in action.
Shows token bucket and sliding window behavior.
"""
import time

from ratelimiter.decorators import rate_limit
from ratelimiter.limiter import RateLimitExceeded, SlidingWindow, TokenBucket


def demo_token_bucket():
    print("=== Token Bucket (capacity=3, rate=1 token/sec) ===")
    bucket = TokenBucket(capacity=3, rate=1.0)

    for i in range(5):
        allowed = bucket.try_consume()
        tokens = bucket.available_tokens
        print(f"  Call {i+1}: {'ALLOWED' if allowed else 'BLOCKED ':7}  tokens left: {tokens:.2f}")

    print("  Waiting 2 seconds for refill...")
    time.sleep(2)
    allowed = bucket.try_consume()
    print(f"  Call 6: {'ALLOWED' if allowed else 'BLOCKED ':7}  tokens left: {bucket.available_tokens:.2f}\n")


def demo_sliding_window():
    print("=== Sliding Window (max_calls=3, window=2s) ===")
    window = SlidingWindow(max_calls=3, window_seconds=2.0)

    for i in range(5):
        allowed = window.try_consume()
        remaining = window.remaining_calls
        print(f"  Call {i+1}: {'ALLOWED' if allowed else 'BLOCKED ':7}  remaining: {remaining}")

    print("  Waiting 2 seconds for window to slide...")
    time.sleep(2)
    allowed = window.try_consume()
    print(f"  Call 6: {'ALLOWED' if allowed else 'BLOCKED ':7}  remaining: {window.remaining_calls}\n")


def demo_decorator():
    print("=== @rate_limit decorator (SlidingWindow, 2 calls/3s) ===")
    limiter = SlidingWindow(max_calls=2, window_seconds=3.0)

    @rate_limit(limiter, raise_on_limit=False)
    def fetch_data(n: int) -> str:
        return f"data-{n}"

    for i in range(4):
        result = fetch_data(i)
        print(f"  fetch_data({i}) → {result if result is not None else 'BLOCKED'}")
    print()


if __name__ == "__main__":
    demo_token_bucket()
    demo_sliding_window()
    demo_decorator()
