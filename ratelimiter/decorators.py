"""
Decorator interface for rate limiters.

Usage:
    from ratelimiter.decorators import rate_limit
    from ratelimiter.limiter import TokenBucket, SlidingWindow

    bucket = TokenBucket(capacity=5, rate=1.0)

    @rate_limit(bucket)
    def my_api_call():
        ...
"""
import functools
from typing import Callable

from .limiter import RateLimitExceeded, SlidingWindow, TokenBucket


def rate_limit(limiter: TokenBucket | SlidingWindow, raise_on_limit: bool = True):
    """
    Wrap a function with a rate limiter.

    If raise_on_limit is True (default), raises RateLimitExceeded.
    If False, returns None when the call is blocked.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if isinstance(limiter, TokenBucket):
                allowed = limiter.try_consume()
            else:
                allowed = limiter.try_consume()

            if not allowed:
                if raise_on_limit:
                    if isinstance(limiter, TokenBucket):
                        limiter.consume()  # will raise with correct retry_after
                    else:
                        limiter.consume()
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator
