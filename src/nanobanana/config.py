"""Configuration management for nanobanana."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")


def get_api_key() -> str:
    """Get the Google API key from environment."""
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        raise ValueError(
            "GOOGLE_API_KEY not found. "
            "Set it in .env file or as environment variable."
        )
    return key


def get_default_model() -> str:
    """Get the default Gemini model for image generation."""
    return os.getenv("GEMINI_MODEL", "gemini-2.0-flash-preview-image-generation")


def get_max_concurrent() -> int:
    """Get the maximum concurrent requests setting."""
    return int(os.getenv("MAX_CONCURRENT", "15"))


def get_rpm_limit() -> int:
    """Get the requests per minute limit."""
    return int(os.getenv("RPM_LIMIT", "50"))


# Available models for image generation
MODELS = {
    "flash": "gemini-2.0-flash-preview-image-generation",
    "pro": "gemini-2.0-flash-preview-image-generation",  # Alias
}

# Directory paths
PROFILES_DIR = PROJECT_ROOT / "profiles"
OUTPUT_DIR = PROJECT_ROOT / "output"


def ensure_output_dir() -> Path:
    """Ensure output directory exists and return path."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def ensure_profiles_dir() -> Path:
    """Ensure profiles directory exists and return path."""
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    return PROFILES_DIR
