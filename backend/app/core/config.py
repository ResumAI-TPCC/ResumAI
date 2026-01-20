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
    llm_provider: str = "gemini"

    # Gemini settings
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    gemini_temperature: float = 0.7
    gemini_max_tokens: int = 2048
    gemini_timeout: float = 60.0
    gemini_max_retries: int = 3
    gemini_retry_delay: float = 1.0


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
