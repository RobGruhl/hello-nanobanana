#!/usr/bin/env python3
"""Example script for testing nanobanana image generation."""

import asyncio
from pathlib import Path

from nanobanana import generate_image, generate_batch


def test_single_image():
    """Test single image generation."""
    print("Testing single image generation...")

    result = generate_image(
        prompt="A majestic dragon perched on a mountain peak at sunset",
        output="output/test_dragon.png",
        aspect_ratio="16:9",
    )

    print(f"  Generated: {result.path}")
    print(f"  Size: {result.width}x{result.height}")
    print(f"  Time: {result.generation_time:.1f}s")


def test_with_profile():
    """Test generation with a profile."""
    print("\nTesting with comic-panel profile...")

    result = generate_image(
        prompt="A hero standing triumphantly",
        output="output/test_hero.png",
        profile="comic-panel",
    )

    print(f"  Generated: {result.path}")
    print(f"  Size: {result.width}x{result.height}")


async def test_batch():
    """Test batch generation."""
    print("\nTesting batch generation...")

    items = [
        {"prompt": "A red dragon breathing fire", "output": "output/batch_dragon.png"},
        {"prompt": "A wizard casting a spell", "output": "output/batch_wizard.png"},
        {"prompt": "A knight in shining armor", "output": "output/batch_knight.png"},
    ]

    results = await generate_batch(items, max_concurrent=3)

    print(f"  Generated {len(results)} images")
    for r in results:
        print(f"    - {r.path.name}: {r.width}x{r.height}")


if __name__ == "__main__":
    # Ensure output directory exists
    Path("output").mkdir(exist_ok=True)

    # Run tests
    test_single_image()
    test_with_profile()
    asyncio.run(test_batch())

    print("\nAll tests completed!")
