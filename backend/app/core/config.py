"""
Application Configuration Module
Uses pydantic-settings to manage environment variables and configuration
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings class"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore undefined environment variables
    )

    # Application settings
    APP_NAME: str = "ResumAI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # API settings
    API_PREFIX: str = "/api"

    # LLM Provider settings
    # Specific provider settings will be extended by each implementation
    LLM_PROVIDER: str = ""

    # GCP / GCS settings
    GCP_PROJECT_ID: str  # Mandatory, fail early if missing
    GCS_BUCKET_NAME: str  # Mandatory, fail early if missing
    GCS_OBJECT_PREFIX: str = "resumes"

@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
