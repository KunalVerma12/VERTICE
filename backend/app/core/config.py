"""Application configuration module using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repository root directory
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    """Application runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "Vértice"
    APP_ENV: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # Template Engine Configuration
    TEMPLATES_DIR: Path = ROOT_DIR / "templates"
    OUTPUT_DIR: Path = ROOT_DIR / "generated"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()


settings = get_settings()
