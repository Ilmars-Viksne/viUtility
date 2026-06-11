"""Application configuration loaded from environment and .env files."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="TEXT_FILE_COLLECTOR_",
        extra="ignore",
    )

    default_encoding: str = Field(default="utf-8")
    binary_detection_chunk_size: int = Field(default=4096, ge=1)
    output_separator_length: int = Field(default=80, ge=1)
    log_level: str = Field(default="INFO")


def load_settings() -> Settings:
    """Load application settings."""
    return Settings()
