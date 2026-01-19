"""
Application Configuration Module
Uses pydantic-settings to manage environment variables and configuration
"""

from functools import lru_cache

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class GeminiConfig(BaseModel):
    """Gemini-specific configuration"""

    api_key: str = ""
    model: str = "gemini-2.5-flash"


class LLMConfig(BaseModel):
    """LLM configuration"""

    provider: str = "gemini"
    gemini: GeminiConfig = GeminiConfig()


class AppConfig(BaseModel):
    """Application configuration"""

    name: str = "ResumAI"
    version: str = "0.1.0"
    debug: bool = False


class APIConfig(BaseModel):
    """API configuration"""

    prefix: str = "/api"


class Settings(BaseSettings):
    """Application settings class - reads from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore undefined environment variables
    )

    # Flat environment variables (read from .env)
    app_name: str = "ResumAI"
    app_version: str = "0.1.0"
    debug: bool = False
    api_prefix: str = "/api"
    llm_provider: str = "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"


class EnvConfig:
    """
    Unified environment configuration.
    All environment variables should be accessed through this class.
    """

    def __init__(self, settings: Settings):
        self._settings = settings

        # Organized configuration structure
        self.app = AppConfig(
            name=settings.app_name,
            version=settings.app_version,
            debug=settings.debug,
        )

        self.api = APIConfig(
            prefix=settings.api_prefix,
        )

        self.llm = LLMConfig(
            provider=settings.llm_provider,
            gemini=GeminiConfig(
                api_key=settings.gemini_api_key,
                model=settings.gemini_model,
            ),
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


@lru_cache
def get_env_config() -> EnvConfig:
    """Get cached env_config instance"""
    return EnvConfig(get_settings())


# For backward compatibility
settings = get_settings()

# Unified environment configuration - use this for all config access
env_config = get_env_config()
