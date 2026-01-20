"""
LLM Provider Factory Module
Returns the appropriate LLM Provider instance based on configuration
"""

from typing import Dict, Optional, Type

from app.core.config import settings

from .base import BaseLLMProvider

# Provider registry
_provider_registry: Dict[str, Type[BaseLLMProvider]] = {}

# Current provider instance cache
_provider_instance: Optional[BaseLLMProvider] = None


def register_provider(name: str, provider_class: Type[BaseLLMProvider]) -> None:
    """
    Register an LLM Provider

    Args:
        name: Provider name (e.g., "openai", "anthropic")
        provider_class: Provider class (must inherit from BaseLLMProvider)

    Example:
        >>> register_provider("openai", OpenAIProvider)
    """
    _provider_registry[name] = provider_class


def get_llm_provider() -> BaseLLMProvider:
    """
    Factory method: returns the appropriate LLM Provider based on configuration

    Returns:
        BaseLLMProvider: LLM Provider instance

    Raises:
        ValueError: No provider registered or unsupported provider type
    """
    global _provider_instance

    if _provider_instance is not None:
        return _provider_instance

    if not _provider_registry:
        raise ValueError(
            "No LLM Provider registered. Please use register_provider() first."
        )

    provider_class = _provider_registry.get(settings.llm_provider)

    if provider_class is None:
        raise ValueError(
            f"Unsupported LLM Provider: {settings.llm_provider}. "
            f"Registered options: {list(_provider_registry.keys())}"
        )

    _provider_instance = provider_class()
    return _provider_instance


def clear_provider_cache() -> None:
    """Clear provider instance cache (for testing or reinitialization)"""
    global _provider_instance
    _provider_instance = None

