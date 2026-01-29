"""Gemini API client wrapper for image generation."""

import asyncio
import logging
import time
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types
from PIL import Image

from .config import get_api_key, get_default_model
from .models.image import ImageConfig, ImageResult

logger = logging.getLogger(__name__)


class GeminiImageClient:
    """Client for Gemini image generation API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the client.

        Args:
            api_key: Google API key. If not provided, reads from environment.
        """
        self._api_key = api_key or get_api_key()
        self._client: Optional[genai.Client] = None

    @property
    def client(self) -> genai.Client:
        """Get or create the Gemini client."""
        if self._client is None:
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def generate(
        self,
        prompt: str,
        output_path: Path,
        config: Optional[ImageConfig] = None,
    ) -> ImageResult:
        """Generate a single image synchronously.

        Args:
            prompt: The text prompt for image generation
            output_path: Path to save the generated image
            config: Image configuration (uses defaults if not provided)

        Returns:
            ImageResult with details about the generated image
        """
        config = config or ImageConfig()
        start_time = time.time()

        # Build generation config
        gen_config = types.GenerateContentConfig(
            response_modalities=config.response_modalities,
            image_config=types.ImageConfig(
                aspect_ratio=config.get_aspect_ratio_string()
            )
        )

        # Generate
        response = self.client.models.generate_content(
            model=config.model,
            contents=prompt,
            config=gen_config
        )

        # Extract and save image
        for part in response.parts:
            if image := part.as_image():
                # Ensure parent directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)
                image.save(str(output_path))

                # Get image dimensions
                pil_img = Image.open(str(output_path))
                width, height = pil_img.size

                generation_time = time.time() - start_time

                return ImageResult(
                    path=output_path,
                    width=width,
                    height=height,
                    prompt=prompt,
                    generation_time=generation_time,
                    model=config.model,
                    aspect_ratio=config.get_aspect_ratio_string(),
                )

        raise RuntimeError("No image in response from Gemini API")

    async def generate_async(
        self,
        prompt: str,
        output_path: Path,
        config: Optional[ImageConfig] = None,
    ) -> ImageResult:
        """Generate a single image asynchronously.

        Runs the synchronous generation in a thread pool to avoid
        blocking the event loop.

        Args:
            prompt: The text prompt for image generation
            output_path: Path to save the generated image
            config: Image configuration (uses defaults if not provided)

        Returns:
            ImageResult with details about the generated image
        """
        return await asyncio.to_thread(
            self.generate,
            prompt,
            output_path,
            config,
        )
