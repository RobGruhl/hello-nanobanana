#!/usr/bin/env python3
"""Basic single image generation with nanobanana.

Generates one image with a text prompt and default settings.
Run: poetry run python examples/01-basic-generation.py
"""

from pathlib import Path
from nanobanana import generate_image

# Ensure output directory exists
Path("output").mkdir(exist_ok=True)

result = generate_image(
    prompt="A majestic mountain landscape at golden hour, dramatic clouds",
    output="output/basic_landscape.png",
    aspect_ratio="16:9",
)

print(f"Generated: {result.path}")
print(f"Size: {result.width}x{result.height}")
print(f"Time: {result.generation_time:.1f}s")
print(f"Model: {result.model}")
