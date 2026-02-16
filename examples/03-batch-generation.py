#!/usr/bin/env python3
"""Batch image generation with adaptive rate limiting.

Generates multiple images concurrently with automatic retry on 429 errors.
The AdaptiveSemaphore adjusts concurrency based on API responses.
Run: poetry run python examples/03-batch-generation.py
"""

import asyncio
import logging
from pathlib import Path
from nanobanana import generate_batch

# Enable logging to see rate limiting in action
logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

# Ensure output directory exists
Path("output/batch").mkdir(parents=True, exist_ok=True)

items = [
    {"prompt": "A red dragon perched on a castle tower", "output": "output/batch/dragon.png"},
    {"prompt": "A wizard casting lightning in a storm", "output": "output/batch/wizard.png"},
    {"prompt": "A knight in golden armor on horseback", "output": "output/batch/knight.png"},
    {"prompt": "An enchanted forest with glowing mushrooms", "output": "output/batch/forest.png"},
    {"prompt": "A pirate ship sailing through a whirlpool", "output": "output/batch/pirate.png"},
]

print(f"Generating {len(items)} images in batch...")
print(f"Rate limiting: adaptive concurrency + 50 RPM token bucket\n")

results = asyncio.run(
    generate_batch(
        items,
        max_concurrent=5,
        rpm_limit=50,
        skip_existing=True,  # Won't regenerate if file already exists
    )
)

print(f"\nCompleted: {len(results)}/{len(items)} images")
for r in results:
    print(f"  {r.path.name}: {r.width}x{r.height} ({r.generation_time:.1f}s)")
