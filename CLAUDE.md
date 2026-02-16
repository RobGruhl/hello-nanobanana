# hello-nanobanana

Python library + CLI for Google Gemini image generation with adaptive rate limiting.

## File Map

```
src/nanobanana/
  __init__.py          # Public API: generate_image, generate_batch, models
  client.py            # GeminiImageClient — wraps google-genai SDK
  generator.py         # generate_image() — single image generation
  batch.py             # generate_batch() — async batch with rate limiting
  rate_limit.py        # AdaptiveSemaphore + RPMLimiter
  config.py            # Env var loading, paths, model aliases
  models/
    image.py           # ImageConfig, ImageResult, AspectRatio (Pydantic)
    profile.py         # GenerationProfile — YAML-based presets
profiles/              # 3 YAML presets: default, comic-panel, cinematic
examples/              # 3 numbered examples (basic, profile, batch)
docs/                  # 2 docs: API reference, rate limiting
```

## Key Operations

**Python API:**
```python
from nanobanana import generate_image, generate_batch
result = generate_image("A sunset", output="sunset.png", aspect_ratio="16:9")
results = await generate_batch([{"prompt": "...", "output": "..."}])
```

**CLI** (installed as `gemini-image`):
```bash
gemini-image generate "prompt" -o out.png --aspect 16:9
gemini-image batch prompts.json --output-dir ./images/ --concurrent 12
gemini-image profiles          # list presets
gemini-image test              # quick API check
```

## Models

| Alias | Model ID | Notes |
|-------|----------|-------|
| flash | gemini-2.0-flash-exp-image-generation | Fast, experimental |
| flash-25 | gemini-2.5-flash-image | Newer flash |
| pro | gemini-3-pro-image-preview | Default, highest quality |

## Key Gotchas

- **Rate limiting is adaptive**: AdaptiveSemaphore starts at 8 concurrent, drops by 2 on 429, increases by 1 every 10 successes. RPMLimiter uses token bucket at 50 req/min default.
- **Aspect ratios are enum-validated**: Only 5 values accepted (2:3, 3:2, 1:1, 16:9, 9:16). Use `AspectRatio.from_string()`.
- **Profiles modify prompts**: style_prefix and style_suffix are prepended/appended to your prompt text.
- **Async batch runs sync generation in thread pool**: `client.generate_async()` uses `asyncio.to_thread()` — the google-genai SDK is synchronous under the hood.
- **Config loads .env from project root**: `config.py` resolves `PROJECT_ROOT` via `__file__` traversal. When copying to another project, update or remove this.

## Copy to New Project

```bash
cp -r src/nanobanana/ /new-project/src/nanobanana/
cp -r profiles/ /new-project/profiles/
# Add to pyproject.toml: google-genai, click, rich, pydantic, python-dotenv, pillow, pyyaml
# Set GOOGLE_API_KEY in .env
```

## Distilled From

Built as a standalone workshop. Rate limiting patterns from everpeak-comic project.
