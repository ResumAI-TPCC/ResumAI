"""
LLM Service Module
Provides unified LLM Provider interface and factory methods
"""

from .base import BaseLLMProvider, LLMResponse, MatchScoreResult
from .factory import get_llm_provider, register_provider
from .gemini import GeminiProvider

# Register Gemini Provider
register_provider("gemini", GeminiProvider)

__all__ = [
    "BaseLLMProvider",
    "LLMResponse",
    "MatchScoreResult",
    "get_llm_provider",
    "register_provider",
    "GeminiProvider",
]
