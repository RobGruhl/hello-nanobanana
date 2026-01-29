"""Image generation data models using Pydantic."""

from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class AspectRatio(str, Enum):
    """Supported aspect ratios for Gemini image generation."""

    PORTRAIT = "2:3"
    LANDSCAPE = "3:2"
    SQUARE = "1:1"
    WIDE = "16:9"
    TALL = "9:16"

    @classmethod
    def from_string(cls, value: str) -> "AspectRatio":
        """Convert a string aspect ratio to enum.

        Accepts both enum names (PORTRAIT) and values (2:3).
        """
        # Try direct value match
        for ratio in cls:
            if ratio.value == value:
                return ratio
        # Try name match
        try:
            return cls[value.upper()]
        except KeyError:
            raise ValueError(
                f"Invalid aspect ratio: {value}. "
                f"Valid options: {[r.value for r in cls]}"
            )


class ImageConfig(BaseModel):
    """Configuration for image generation."""

    model: str = Field(
        default="gemini-2.0-flash-preview-image-generation",
        description="Gemini model ID for image generation"
    )
    aspect_ratio: AspectRatio = Field(
        default=AspectRatio.PORTRAIT,
        description="Aspect ratio for generated images"
    )
    response_modalities: list[str] = Field(
        default_factory=lambda: ["Image"],
        description="Response modalities (should include 'Image')"
    )

    def get_aspect_ratio_string(self) -> str:
        """Get the aspect ratio as a string value."""
        return self.aspect_ratio.value


class ImageResult(BaseModel):
    """Result of an image generation."""

    path: Path = Field(description="Path to the generated image file")
    width: int = Field(description="Image width in pixels")
    height: int = Field(description="Image height in pixels")
    prompt: str = Field(description="The prompt used to generate the image")
    generation_time: float = Field(description="Time taken to generate in seconds")
    model: str = Field(description="Model used for generation")
    aspect_ratio: str = Field(description="Aspect ratio used")

    class Config:
        arbitrary_types_allowed = True
