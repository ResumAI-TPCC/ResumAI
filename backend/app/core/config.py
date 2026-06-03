"""
Application Configuration Module
Uses pydantic-settings to manage environment variables and configuration
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

from dotenv import load_dotenv
# Get the path to .env file (backend/.env)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"
LOCAL_ENV_FILE = BASE_DIR / ".env.local"

# Load .env file explicitly into environment variables
load_dotenv(ENV_FILE, override=False)
load_dotenv(LOCAL_ENV_FILE, override=True)


class Settings(BaseSettings):
    """Application settings class - reads from environment variables"""

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",  # Ignore undefined environment variables
    )

    # Flat environment variables (read from .env)
    APP_NAME: str = "ResumAI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api"

    # LLM Provider settings
    LLM_PROVIDER: str = "gemini"

    # Gemini settings
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_TEMPERATURE: float = 0.7
    GEMINI_MAX_TOKENS: int = 8192
    GEMINI_TIMEOUT: float = 60.0
    GEMINI_MAX_RETRIES: int = 3
    GEMINI_RETRY_DELAY: float = 1.0

    # GCP / GCS settings
    GCP_PROJECT_ID: str = ""  # Mandatory, fail early if missing
    GCS_BUCKET_NAME: str = ""  # Mandatory, fail early if missing
    GCS_OBJECT_PREFIX: str = "resumes"
    GCP_SA_KEY: str = ""
    GCP_PRIVATE_KEY: str = ""
    GCP_PRIVATE_KEY_ID: str = ""

    # Firebase Auth settings
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_SERVICE_ACCOUNT_KEY: str = ""
    FIREBASE_CREDENTIALS_PATH: str = ""

    # Local development auth bypass. Only active when DEBUG=true.
    DEV_AUTH_TOKEN: str = ""
    DEV_AUTH_EMAIL: str = ""
    DEV_AUTH_DISPLAY_NAME: str = "Local Test User"
    DEV_AUTH_UID: str = "local-test-user"

    # Security settings
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # File upload settings
    MAX_FILE_SIZE_MB: int = 5
    SESSION_EXPIRY_HOURS: int = 24

@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# For backward compatibility
settings = get_settings()
