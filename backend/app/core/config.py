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
    APP_NAME: str = "ResumAI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api"
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # GCP / GCS settings
    GCP_PROJECT_ID: str  # Mandatory, fail early if missing
    GCS_BUCKET_NAME: str  # Mandatory, fail early if missing
    GCS_OBJECT_PREFIX: str = "resumes"


class EnvConfig:
    """
    Unified environment configuration.
    All environment variables should be accessed through this class.
    """

    def __init__(self, settings: Settings):
        self._settings = settings

        # Organized configuration structure
        self.app = AppConfig(
            name=settings.APP_NAME,
            version=settings.APP_VERSION,
            debug=settings.DEBUG,
        )

        self.api = APIConfig(
            prefix=settings.API_PREFIX,
        )

        self.llm = LLMConfig(
            provider=settings.LLM_PROVIDER,
            gemini=GeminiConfig(
                api_key=settings.GEMINI_API_KEY,
                model=settings.GEMINI_MODEL,
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
