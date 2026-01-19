"""
LLM Service Module
Provides unified LLM Provider interface and factory methods
"""

from .base import BaseLLMProvider, LLMResponse, MatchScoreResult
from .factory import get_llm_provider, register_provider, clear_provider_cache
from .exceptions import (
    LLMException,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMResponseError,
    LLMServiceUnavailableError,
)
from .gemini_provider import GeminiProvider, send_to_gemini

# Register Gemini provider
register_provider("gemini", GeminiProvider)

__all__ = [
    # Base classes
    "BaseLLMProvider",
    "LLMResponse",
    "MatchScoreResult",
    # Factory
    "get_llm_provider",
    "register_provider",
    "clear_provider_cache",
    # Exceptions
    "LLMException",
    "LLMAuthenticationError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "LLMResponseError",
    "LLMServiceUnavailableError",
    # Providers
    "GeminiProvider",
    "send_to_gemini",
]
