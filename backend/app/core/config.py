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
    app_name: str = "ResumAI"
    app_version: str = "0.1.0"
    debug: bool = False

    # API settings
    api_prefix: str = "/api"

    # LLM Provider settings
    # Specific provider settings will be extended by each implementation
    llm_provider: str = ""

    # GCP / GCS settings
    gcp_project_id: str = ""
    gcs_bucket_name: str = ""
    gcs_object_prefix: str = "resumes"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()