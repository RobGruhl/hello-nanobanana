"""Single image generation functions."""

from pathlib import Path
from typing import Optional, Union

from .client import GeminiImageClient
from .config import get_default_model
from .models.image import ImageConfig, ImageResult, AspectRatio
from .models.profile import GenerationProfile, load_profile


def generate_image(
    prompt: str,
    output: Union[Path, str],
    aspect_ratio: str = "2:3",
    model: Optional[str] = None,
    profile: Optional[str] = None,
    api_key: Optional[str] = None,
) -> ImageResult:
    """Generate a single image.

    This is the main public API for simple image generation.

    Args:
        prompt: Text description of the image to generate
        output: Path to save the generated image
        aspect_ratio: Aspect ratio (e.g., "2:3", "16:9", "1:1")
        model: Gemini model ID (uses default if not provided)
        profile: Profile ID to load settings from
        api_key: Google API key (uses environment if not provided)

    Returns:
        ImageResult with details about the generated image

    Examples:
        >>> result = generate_image(
        ...     "A sunset over mountains",
        ...     "sunset.png",
        ...     aspect_ratio="16:9"
        ... )
        >>> print(f"Generated: {result.path} ({result.width}x{result.height})")
    """
    output_path = Path(output)

    # Load profile if specified
    gen_profile: Optional[GenerationProfile] = None
    if profile:
        gen_profile = load_profile(profile)

    # Build config
    if gen_profile:
        config = gen_profile.config
        # Apply profile's style to prompt
        formatted_prompt = gen_profile.format_prompt(prompt)
    else:
        config = ImageConfig(
            model=model or get_default_model(),
            aspect_ratio=AspectRatio.from_string(aspect_ratio),
        )
        formatted_prompt = prompt

    # Override model if explicitly specified
    if model:
        config = config.model_copy(update={"model": model})

    # Generate
    client = GeminiImageClient(api_key=api_key)
    return client.generate(formatted_prompt, output_path, config)
