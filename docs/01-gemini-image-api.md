# Gemini Image Generation API Reference

## Overview

Nanobanana uses the Google Gemini API via the `google-genai` Python SDK to generate images from text prompts. The API returns images as part of multimodal responses.

## Authentication

Requires a `GOOGLE_API_KEY` with Gemini API access. Get one from [Google AI Studio](https://aistudio.google.com/).

## API Call Pattern

```python
from google import genai
from google.genai import types

client = genai.Client(api_key="...")

response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents="A sunset over mountains",
    config=types.GenerateContentConfig(
        response_modalities=["Image"],
        image_config=types.ImageConfig(aspect_ratio="16:9")
    )
)

# Extract image from response parts
for part in response.parts:
    if image := part.as_image():
        image.save("output.png")
```

## Available Models

| Model ID | Type | Notes |
|----------|------|-------|
| `gemini-2.0-flash-exp-image-generation` | Flash | Fast, experimental |
| `gemini-2.5-flash-image` | Flash | Newer flash generation |
| `gemini-3-pro-image-preview` | Pro | Default — highest quality |

## Aspect Ratios

The API accepts these aspect ratio strings in `ImageConfig`:

| Value | Name | Typical Use |
|-------|------|-------------|
| `2:3` | Portrait | Characters, mobile |
| `3:2` | Landscape | Scenes, desktop |
| `1:1` | Square | Social media, icons |
| `16:9` | Wide | Cinematic, panoramas |
| `9:16` | Tall | Stories, posters |

Other values are rejected by the API.

## Response Format

The response is a `GenerateContentResponse`. Images are in `response.parts` as `Part` objects. Use `part.as_image()` to get a PIL-compatible image object, then `.save()` to write to disk.

If the prompt violates content policies, the response may contain no image parts — check for this.

## Key Dependencies

- `google-genai` >= 1.0 — Official Google Generative AI SDK
- `Pillow` >= 10.0 — Used to read image dimensions after saving

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | (required) | API key with Gemini access |
| `GEMINI_MODEL` | `gemini-3-pro-image-preview` | Default model |
| `MAX_CONCURRENT` | `15` | Max concurrent batch requests |
| `RPM_LIMIT` | `50` | Requests per minute limit |
