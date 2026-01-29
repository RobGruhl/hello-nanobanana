"""Generation profile data models using Pydantic."""

from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel, Field

from .image import ImageConfig, AspectRatio


class GenerationProfile(BaseModel):
    """A reusable profile for image generation with presets."""

    id: str = Field(description="Unique identifier for the profile")
    name: str = Field(description="Human-readable name")
    description: str = Field(default="", description="Description of the profile")

    config: ImageConfig = Field(
        default_factory=ImageConfig,
        description="Image generation configuration"
    )

    style_prefix: str = Field(
        default="",
        description="Text prepended to all prompts"
    )
    style_suffix: str = Field(
        default="",
        description="Text appended to all prompts"
    )

    def format_prompt(self, prompt: str) -> str:
        """Format a prompt with the profile's style prefix and suffix."""
        parts = []
        if self.style_prefix:
            parts.append(self.style_prefix)
        parts.append(prompt)
        if self.style_suffix:
            parts.append(self.style_suffix)
        return " ".join(parts)

    @classmethod
    def from_yaml(cls, path: Path) -> "GenerationProfile":
        """Load a profile from a YAML file."""
        with open(path, "r") as f:
            data = yaml.safe_load(f)

        # Handle nested config
        if "config" in data:
            config_data = data["config"]
            # Convert aspect_ratio string to enum if present
            if "aspect_ratio" in config_data:
                config_data["aspect_ratio"] = AspectRatio.from_string(
                    config_data["aspect_ratio"]
                )
            data["config"] = ImageConfig(**config_data)

        return cls(**data)

    def to_yaml(self, path: Path) -> None:
        """Save the profile to a YAML file."""
        data = self.model_dump()
        # Convert enums to strings for YAML
        if "config" in data and "aspect_ratio" in data["config"]:
            data["config"]["aspect_ratio"] = data["config"]["aspect_ratio"].value if hasattr(data["config"]["aspect_ratio"], "value") else str(data["config"]["aspect_ratio"])

        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def load_profile(profile_id: str, profiles_dir: Optional[Path] = None) -> GenerationProfile:
    """Load a profile by ID from the profiles directory."""
    from ..config import PROFILES_DIR

    search_dir = profiles_dir or PROFILES_DIR

    # Try with .yaml extension
    yaml_path = search_dir / f"{profile_id}.yaml"
    if yaml_path.exists():
        return GenerationProfile.from_yaml(yaml_path)

    # Try with .yml extension
    yml_path = search_dir / f"{profile_id}.yml"
    if yml_path.exists():
        return GenerationProfile.from_yaml(yml_path)

    raise FileNotFoundError(f"Profile '{profile_id}' not found in {search_dir}")


def list_profiles(profiles_dir: Optional[Path] = None) -> list[str]:
    """List available profile IDs."""
    from ..config import PROFILES_DIR

    search_dir = profiles_dir or PROFILES_DIR

    if not search_dir.exists():
        return []

    profiles = []
    for path in search_dir.glob("*.yaml"):
        profiles.append(path.stem)
    for path in search_dir.glob("*.yml"):
        if path.stem not in profiles:
            profiles.append(path.stem)

    return sorted(profiles)
