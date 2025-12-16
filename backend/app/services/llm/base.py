"""
LLM Provider Abstract Base Class
Defines the interface that all LLM Providers must implement
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, List, Optional


@dataclass
class LLMResponse:
    """LLM response data class"""

    content: str
    model: str
    usage: Optional[dict] = None
    finish_reason: Optional[str] = None


@dataclass
class Message:
    """Message data class"""

    role: str  # "system", "user", "assistant"
    content: str


class BaseLLMProvider(ABC):
    """
    LLM Provider Abstract Base Class

    All LLM Provider implementations must inherit from this class and implement:
    - chat: Synchronous chat completion
    - chat_stream: Streaming chat completion
    """

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Send chat request and get complete response

        Args:
            messages: List of messages
            temperature: Temperature parameter, controls randomness
            max_tokens: Maximum number of tokens to generate

        Returns:
            LLMResponse: Contains response content and metadata
        """
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """
        Send chat request and return response as a stream

        Args:
            messages: List of messages
            temperature: Temperature parameter
            max_tokens: Maximum number of tokens to generate

        Yields:
            str: Response text chunks
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name"""
        pass

