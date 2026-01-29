"""Adaptive rate limiting for Gemini API requests.

Battle-tested rate limiting from everpeak-comic project.
"""

import asyncio
import logging
import time

logger = logging.getLogger(__name__)


class AdaptiveSemaphore:
    """Semaphore with adaptive concurrency based on rate limit responses.

    Automatically adjusts concurrency:
    - Decreases when hitting 429 errors
    - Increases when requests succeed consistently
    """

    def __init__(
        self,
        initial_value: int = 8,
        min_value: int = 2,
        max_value: int = 20
    ):
        self.value = initial_value
        self.min_value = min_value
        self.max_value = max_value
        self._semaphore = asyncio.Semaphore(initial_value)
        self._lock = asyncio.Lock()
        self._current_permits = initial_value
        self._success_count = 0

    async def acquire(self):
        """Acquire a permit."""
        await self._semaphore.acquire()

    def release(self):
        """Release a permit."""
        self._semaphore.release()

    async def __aenter__(self):
        """Context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()
        return False

    async def increase_concurrency(self):
        """Increase concurrency when things are going well."""
        async with self._lock:
            if self._current_permits < self.max_value:
                old = self._current_permits
                self._current_permits = min(self._current_permits + 1, self.max_value)
                # Add a new permit
                self._semaphore.release()
                logger.info(f"Increased concurrency: {old} -> {self._current_permits}")

    async def decrease_concurrency(self):
        """Decrease concurrency when hitting rate limits."""
        async with self._lock:
            if self._current_permits > self.min_value:
                old = self._current_permits
                self._current_permits = max(self._current_permits - 2, self.min_value)
                # Remove permits by acquiring without releasing
                try:
                    for _ in range(min(2, old - self._current_permits)):
                        self._semaphore.acquire_nowait()
                except Exception:
                    pass
                logger.warning(f"Decreased concurrency: {old} -> {self._current_permits}")

    def get_current(self) -> int:
        """Get current concurrency level."""
        return self._current_permits

    async def report_success(self):
        """Report a successful request. May increase concurrency."""
        async with self._lock:
            self._success_count += 1
            # Increase concurrency every 10 successes
            if self._success_count % 10 == 0:
                await self.increase_concurrency()

    async def report_rate_limit(self):
        """Report a rate limit error. Decreases concurrency."""
        await self.decrease_concurrency()
        self._success_count = 0  # Reset success count


class RPMLimiter:
    """Token bucket rate limiter for requests per minute.

    Ensures we don't exceed the API's requests-per-minute limit
    by using a token bucket algorithm.
    """

    def __init__(self, max_per_minute: int = 50):
        self.max_per_minute = max_per_minute
        self.capacity = float(max_per_minute)
        self.last_update = time.time()
        self.lock = asyncio.Lock()

    async def acquire(self):
        """Acquire permission to make a request. Blocks if rate limited."""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update

            # Refill capacity based on time elapsed
            self.capacity = min(
                self.capacity + (self.max_per_minute * elapsed / 60.0),
                self.max_per_minute
            )
            self.last_update = now

            # Wait if no capacity
            while self.capacity < 1.0:
                await asyncio.sleep(0.1)
                now = time.time()
                elapsed = now - self.last_update
                self.capacity = min(
                    self.capacity + (self.max_per_minute * elapsed / 60.0),
                    self.max_per_minute
                )
                self.last_update = now

            # Consume one token
            self.capacity -= 1.0

    async def __aenter__(self):
        """Context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        return False

    def get_available(self) -> float:
        """Get the current available capacity."""
        now = time.time()
        elapsed = now - self.last_update
        return min(
            self.capacity + (self.max_per_minute * elapsed / 60.0),
            self.max_per_minute
        )
