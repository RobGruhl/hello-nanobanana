#!/usr/bin/env python3
"""Image generation using YAML profiles.

Profiles add style_prefix and style_suffix to your prompt automatically.
Available profiles: default, comic-panel, cinematic.
Run: poetry run python examples/02-with-profile.py
"""

from pathlib import Path
from nanobanana import generate_image
from nanobanana.models.profile import load_profile, list_profiles

# Ensure output directory exists
Path("output").mkdir(exist_ok=True)

# List available profiles
print("Available profiles:", list_profiles())

# Generate with comic-panel profile
print("\nGenerating with comic-panel profile...")
result = generate_image(
    prompt="A hero standing on a cliff overlooking a vast city",
    output="output/comic_hero.png",
    profile="comic-panel",
)
print(f"Generated: {result.path} ({result.width}x{result.height})")

# Generate with cinematic profile
print("\nGenerating with cinematic profile...")
result = generate_image(
    prompt="A lone figure walking through a neon-lit alley in the rain",
    output="output/cinematic_alley.png",
    profile="cinematic",
)
print(f"Generated: {result.path} ({result.width}x{result.height})")

# Show how the profile transforms the prompt
prof = load_profile("comic-panel")
raw_prompt = "A dragon breathing fire"
formatted = prof.format_prompt(raw_prompt)
print(f"\nProfile prompt formatting:")
print(f"  Raw:       {raw_prompt}")
print(f"  Formatted: {formatted}")
