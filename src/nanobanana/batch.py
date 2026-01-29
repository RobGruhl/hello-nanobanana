"""Batch image generation with adaptive rate limiting."""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Union
from dataclasses import dataclass

from .client import GeminiImageClient
from .config import get_max_concurrent, get_rpm_limit
from .models.image import ImageConfig, ImageResult
from .models.profile import GenerationProfile, load_profile
from .rate_limit import AdaptiveSemaphore, RPMLimiter

logger = logging.getLogger(__name__)


@dataclass
class BatchItem:
    """A single item in a batch generation request."""
    prompt: str
    output: Union[Path, str]
    config: Optional[ImageConfig] = None


@dataclass
class BatchStats:
    """Statistics from a batch generation run."""
    total: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    rate_limited: int = 0


async def generate_batch(
    items: list[dict],
    config: Optional[ImageConfig] = None,
    profile: Optional[str] = None,
    max_concurrent: Optional[int] = None,
    rpm_limit: Optional[int] = None,
    skip_existing: bool = True,
    api_key: Optional[str] = None,
) -> list[ImageResult]:
    """Generate multiple images with adaptive rate limiting.

    This function handles batch generation with:
    - Automatic retry with exponential backoff
    - Adaptive concurrency based on API responses
    - Token bucket rate limiting for RPM
    - Optional skipping of existing files

    Args:
        items: List of dicts with "prompt" and "output" keys
        config: Shared ImageConfig for all items (can be overridden per-item)
        profile: Profile ID to load settings from
        max_concurrent: Maximum concurrent requests (default from env)
        rpm_limit: Requests per minute limit (default from env)
        skip_existing: Skip items where output file already exists
        api_key: Google API key (uses environment if not provided)

    Returns:
        List of ImageResult for successful generations

    Examples:
        >>> results = await generate_batch([
        ...     {"prompt": "A red dragon", "output": "dragon.png"},
        ...     {"prompt": "A blue wizard", "output": "wizard.png"},
        ... ], max_concurrent=10)
    """
    # Load profile if specified
    gen_profile: Optional[GenerationProfile] = None
    if profile:
        gen_profile = load_profile(profile)
        if not config:
            config = gen_profile.config

    # Set up rate limiters
    concurrent = max_concurrent or get_max_concurrent()
    rpm = rpm_limit or get_rpm_limit()

    semaphore = AdaptiveSemaphore(
        initial_value=min(concurrent, 8),  # Start conservative
        min_value=2,
        max_value=concurrent,
    )
    rate_limiter = RPMLimiter(max_per_minute=rpm)

    # Track stats
    stats = BatchStats(total=len(items))
    results: list[ImageResult] = []
    results_lock = asyncio.Lock()

    # Create client
    client = GeminiImageClient(api_key=api_key)

    async def process_item(item: dict) -> Optional[ImageResult]:
        """Process a single batch item with retry logic."""
        prompt = item["prompt"]
        output_path = Path(item["output"])
        item_config = item.get("config", config)

        # Skip if exists
        if skip_existing and output_path.exists():
            logger.info(f"Skipped (exists): {output_path}")
            stats.skipped += 1
            return None

        # Format prompt with profile
        if gen_profile:
            formatted_prompt = gen_profile.format_prompt(prompt)
        else:
            formatted_prompt = prompt

        # Retry logic
        max_retries = 5
        base_delay = 2

        for attempt in range(max_retries):
            try:
                # Acquire rate limiting tokens
                await semaphore.acquire()
                await rate_limiter.acquire()

                try:
                    result = await client.generate_async(
                        formatted_prompt,
                        output_path,
                        item_config,
                    )

                    stats.successful += 1
                    await semaphore.report_success()

                    logger.info(
                        f"Generated: {output_path.name} "
                        f"({result.width}x{result.height})"
                    )

                    return result

                finally:
                    semaphore.release()

            except Exception as e:
                error_str = str(e)

                # Handle rate limiting
                if "429" in error_str or "rate limit" in error_str.lower():
                    stats.rate_limited += 1
                    await semaphore.report_rate_limit()
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"Rate limited: {output_path.name}, "
                        f"retry {attempt + 1}/{max_retries} in {delay}s"
                    )
                    await asyncio.sleep(delay)
                    continue

                # Handle 503 (service overload)
                elif "503" in error_str:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"Service overloaded: {output_path.name}, "
                        f"retry {attempt + 1}/{max_retries} in {delay}s"
                    )
                    await asyncio.sleep(delay)
                    continue

                # Other errors - don't retry
                else:
                    logger.error(f"Failed: {output_path.name} - {e}")
                    stats.failed += 1
                    return None

        # Max retries exhausted
        logger.error(f"Failed after {max_retries} attempts: {output_path.name}")
        stats.failed += 1
        return None

    # Process all items
    tasks = [process_item(item) for item in items]
    all_results = await asyncio.gather(*tasks)

    # Collect successful results
    results = [r for r in all_results if r is not None]

    # Log summary
    logger.info(
        f"Batch complete: {stats.successful}/{stats.total} successful, "
        f"{stats.skipped} skipped, {stats.failed} failed, "
        f"{stats.rate_limited} rate limited"
    )

    return results


def run_batch(
    items: list[dict],
    config: Optional[ImageConfig] = None,
    profile: Optional[str] = None,
    max_concurrent: Optional[int] = None,
    rpm_limit: Optional[int] = None,
    skip_existing: bool = True,
    api_key: Optional[str] = None,
) -> list[ImageResult]:
    """Synchronous wrapper for generate_batch.

    Convenience function for running batch generation from synchronous code.
    See generate_batch for full documentation.
    """
    return asyncio.run(
        generate_batch(
            items=items,
            config=config,
            profile=profile,
            max_concurrent=max_concurrent,
            rpm_limit=rpm_limit,
            skip_existing=skip_existing,
            api_key=api_key,
        )
    )
