"""Application configuration loaded from environment variables."""
from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    """Application settings sourced from environment / .env file."""

    GEMINI_API_KEY: str | None = Field(default=None, description="Primary Google Gemini API key")
    GEMINI_API_KEYS: str | None = Field(default=None, description="Comma-separated list of Gemini API keys for rotation")
    DEFAULT_MODEL: str = Field(
        default="gemini-2.5-pro",
        description="Default Gemini model to use for compilation",
    )
    AVAILABLE_MODELS: List[str] = Field(
        default=["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"],
        description="Models available for selection",
    )
    MAX_REPAIR_CYCLES: int = Field(
        default=3,
        description="Maximum number of validation-repair loops",
    )
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    CORS_ORIGINS: List[str] = Field(
        default=["*"],
        description="Allowed CORS origins",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def api_keys(self) -> List[str]:
        """Return a list of all configured API keys for rotation."""
        keys = []
        if self.GEMINI_API_KEYS:
            keys.extend([k.strip() for k in self.GEMINI_API_KEYS.split(",") if k.strip()])
        if self.GEMINI_API_KEY and self.GEMINI_API_KEY not in keys:
            keys.append(self.GEMINI_API_KEY)
        return keys

# Singleton instance
config: Settings = Settings()

def get_settings() -> Settings:
    """Return the cached settings singleton."""
    return config
