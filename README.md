# api-rate-limiter

A pure-Python rate limiting library implementing two battle-tested algorithms:

- **Token Bucket** — allows bursts up to a configured capacity, refilled at a steady rate
- **Sliding Window** — allows at most N calls per rolling time window

Thread-safe, zero external dependencies, and usable as a function decorator.

## Installation

```bash
pip install -r requirements.txt   # only pytest for tests
```

## Usage

### Token Bucket

```python
from ratelimiter.limiter import TokenBucket, RateLimitExceeded

bucket = TokenBucket(capacity=10, rate=2.0)  # 2 tokens/sec, burst up to 10

bucket.consume()            # raises RateLimitExceeded if empty
bucket.try_consume()        # returns True/False instead
print(bucket.available_tokens)
```

### Sliding Window

```python
from ratelimiter.limiter import SlidingWindow

window = SlidingWindow(max_calls=5, window_seconds=60.0)  # 5 req/min

window.try_consume()        # True if allowed
print(window.remaining_calls)
```

### Decorator

```python
from ratelimiter.decorators import rate_limit
from ratelimiter.limiter import SlidingWindow

limiter = SlidingWindow(max_calls=3, window_seconds=10.0)

@rate_limit(limiter, raise_on_limit=False)  # returns None when blocked
def call_external_api():
    ...
```

## Example output

```
$ python main.py
=== Token Bucket (capacity=3, rate=1 token/sec) ===
  Call 1: ALLOWED   tokens left: 2.00
  Call 2: ALLOWED   tokens left: 1.00
  Call 3: ALLOWED   tokens left: 0.00
  Call 4: BLOCKED   tokens left: 0.00
  Call 5: BLOCKED   tokens left: 0.00
  Waiting 2 seconds for refill...
  Call 6: ALLOWED   tokens left: 1.00
```

## Running tests

```bash
pytest tests/
```

## Project structure

```
api-rate-limiter/
├── ratelimiter/
│   ├── limiter.py      # TokenBucket and SlidingWindow
│   └── decorators.py   # @rate_limit decorator
├── tests/
│   └── test_limiter.py
├── main.py             # Interactive demo
└── requirements.txt
```
