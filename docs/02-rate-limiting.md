# Rate Limiting in Nanobanana

## Overview

Nanobanana uses two complementary rate limiting mechanisms for batch generation: an **AdaptiveSemaphore** for concurrency control and an **RPMLimiter** for requests-per-minute throttling. Both are in `src/nanobanana/rate_limit.py`.

## AdaptiveSemaphore

Controls how many requests run simultaneously. Unlike a fixed semaphore, it adjusts based on API feedback.

### Behavior

- **Initial concurrency**: Starts at `min(max_concurrent, 8)` — conservative start
- **On 429 error**: Drops concurrency by 2 (minimum floor: 2)
- **On success**: Tracks consecutive successes. Every 10 successes, increases concurrency by 1 (up to `max_value`)
- **Success counter resets** on any rate limit hit

### Configuration

```python
semaphore = AdaptiveSemaphore(
    initial_value=8,   # Starting concurrency
    min_value=2,       # Never go below this
    max_value=20,      # Never exceed this
)
```

### How It Works Internally

Uses `asyncio.Semaphore` under the hood:
- **Increase**: Calls `semaphore.release()` to add a permit
- **Decrease**: Calls `semaphore.acquire_nowait()` to consume permits without releasing them

This means the adaptation happens transparently to callers using `async with semaphore`.

## RPMLimiter

Token bucket algorithm that ensures requests don't exceed a per-minute rate.

### Behavior

- Bucket starts full at `max_per_minute` tokens
- Each request consumes 1 token
- Tokens refill continuously based on elapsed time: `capacity += (max_per_minute * elapsed / 60)`
- When no tokens available, blocks with `asyncio.sleep(0.1)` polling

### Configuration

```python
limiter = RPMLimiter(max_per_minute=50)
```

Default is 50 RPM, configurable via `RPM_LIMIT` env var.

## How Batch Uses Both

In `batch.py`, each request must acquire both:

```
1. await semaphore.acquire()    # Concurrency gate
2. await rate_limiter.acquire() # RPM gate
3. ... make API call ...
4. semaphore.release()          # Free concurrency slot
```

Plus retry logic:
- **429 errors**: Report to semaphore (decreases concurrency), exponential backoff (2s, 4s, 8s, 16s, 32s), up to 5 retries
- **503 errors**: Exponential backoff only (no concurrency adjustment)
- **Other errors**: Fail immediately, no retry

## Tuning Tips

- **Start conservative**: Default 8 concurrent is safe for most API tiers
- **Watch for 429 cascades**: If you see rapid concurrency drops in logs, lower `MAX_CONCURRENT`
- **RPM vs concurrency**: RPM limits total throughput; concurrency limits parallelism. Both matter.
- **Enable logging** to see adaptation: `logging.basicConfig(level=logging.INFO)`
