# Nanobanana

High-quality Python library and CLI for Google Gemini image generation with adaptive rate limiting.

## Features

- **Python SDK** - Clean API for single and batch image generation
- **CLI Tool** - Click-based CLI for command-line usage
- **Adaptive Rate Limiting** - Battle-tested rate limiting that adjusts concurrency based on API responses
- **Profile System** - YAML-based image generation presets
- **Async Batch Processing** - Parallel generation with automatic retry and exponential backoff

## Installation

```bash
cd hello-nanobanana
poetry install
```

## Configuration

Copy `example.env` to `.env` and add your Google API key:

```bash
cp example.env .env
# Edit .env and set GOOGLE_API_KEY
```

## Usage

### Python API

```python
from nanobanana import generate_image, generate_batch

# Generate a single image
result = generate_image(
    "A cyberpunk city at night",
    output="cyberpunk.png",
    aspect_ratio="16:9"
)
print(f"Generated: {result.path} ({result.width}x{result.height})")

# Generate with a profile
result = generate_image(
    "Hero standing on a cliff",
    output="hero.png",
    profile="comic-panel"
)

# Batch generation with rate limiting
import asyncio

results = asyncio.run(generate_batch([
    {"prompt": "A red dragon", "output": "dragon.png"},
    {"prompt": "A blue wizard", "output": "wizard.png"},
    {"prompt": "A green forest", "output": "forest.png"},
], max_concurrent=10))
```

### CLI

```bash
# Generate a single image
gemini-image generate "A sunset over mountains" -o sunset.png

# Generate with specific aspect ratio
gemini-image generate "Wide landscape" -o landscape.png --aspect 16:9

# Generate with a profile
gemini-image generate "Hero portrait" --profile comic-panel -o hero.png

# Batch generation from JSON
gemini-image batch prompts.json --output-dir ./images/ --concurrent 12

# List available profiles
gemini-image profiles

# Show profile details
gemini-image info comic-panel

# Quick API test
gemini-image test

# Show available aspect ratios
gemini-image aspect-ratios
```

### Batch JSON Format

Create a JSON file with prompts:

```json
[
    {"prompt": "A red dragon", "output": "dragon.png"},
    {"prompt": "A blue wizard", "output": "wizard.png"},
    {"prompt": "A green forest"}
]
```

If `output` is omitted, filenames are generated automatically.

## Profiles

Profiles are YAML files in the `profiles/` directory that define generation presets:

```yaml
id: comic-panel
name: Comic Book Panel
description: Professional comic book style panel illustrations

config:
  model: gemini-3-pro-image-preview
  aspect_ratio: "2:3"

style_prefix: "Professional comic book panel illustration."
style_suffix: "Clean linework, vibrant colors, dynamic composition."
```

### Available Aspect Ratios

| Name | Value | Use Case |
|------|-------|----------|
| PORTRAIT | 2:3 | Portraits, characters, mobile screens |
| LANDSCAPE | 3:2 | Scenes, landscapes, desktop backgrounds |
| SQUARE | 1:1 | Social media, icons, thumbnails |
| WIDE | 16:9 | Cinematic, panoramas, video thumbnails |
| TALL | 9:16 | Stories, mobile full-screen, posters |

## Rate Limiting

The library includes two rate limiting mechanisms:

### AdaptiveSemaphore

Adjusts concurrency based on API responses:
- Decreases when hitting 429 (rate limit) errors
- Gradually increases when requests succeed consistently
- Configurable min/max concurrency bounds

### RPMLimiter

Token bucket algorithm for requests-per-minute limiting:
- Ensures smooth request distribution
- Prevents burst-induced rate limits

Default limits can be configured via environment variables:

```bash
MAX_CONCURRENT=15  # Maximum concurrent requests
RPM_LIMIT=50       # Requests per minute
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | (required) | Google API key with Gemini access |
| `GEMINI_MODEL` | `gemini-3-pro-image-preview` | Default model |
| `MAX_CONCURRENT` | `15` | Maximum concurrent requests |
| `RPM_LIMIT` | `50` | Requests per minute limit |

## Project Structure

```
hello-nanobanana/
├── src/
│   └── nanobanana/
│       ├── __init__.py       # Public API exports
│       ├── cli.py            # Click CLI commands
│       ├── config.py         # Environment and path configuration
│       ├── client.py         # Gemini API client wrapper
│       ├── models/
│       │   ├── image.py      # ImageConfig, ImageResult models
│       │   └── profile.py    # GenerationProfile for presets
│       ├── generator.py      # Single image generation
│       ├── batch.py          # Batch generation with rate limiting
│       └── rate_limit.py     # AdaptiveSemaphore, RPMLimiter
├── profiles/                 # Generation profiles
│   ├── default.yaml
│   ├── comic-panel.yaml
│   └── cinematic.yaml
├── pyproject.toml
└── example.env
```
