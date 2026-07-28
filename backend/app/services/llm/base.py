"""
LLM Provider Abstract Base Class
Defines the interface that all LLM Providers must implement.

Provider methods now accept List[BaseMessage] (assembled by PromptBuilder
via ChatPromptTemplate) and return typed Pydantic models instead of raw
strings, eliminating manual JSON parsing in the service layer.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from langchain_core.messages import BaseMessage

from .schemas import AnalyzeResult, MatchResult


@dataclass
class LLMResponse:
    """Raw LLM response — used for free-text operations (optimize)."""

    content: str
    model: str
    usage: Optional[dict] = None


@dataclass
class MatchScoreResult:
    """Legacy match result dataclass — kept for backward compatibility."""

    score: float
    explanation: str
    suggestions: List[str]


class BaseLLMProvider(ABC):
    """
    LLM Provider Abstract Base Class.

    All implementations must accept List[BaseMessage] as input and return
    typed results:
      analyze  → AnalyzeResult  (via with_structured_output)
      match    → MatchResult    (via with_structured_output)
      optimize → LLMResponse    (free-text Markdown)
    """

    @abstractmethod
    async def analyze(self, messages: List[BaseMessage]) -> AnalyzeResult:
        """
        Analyze resume and return structured improvement suggestions.

        Args:
            messages: Formatted prompt messages from PromptBuilder.

        Returns:
            AnalyzeResult: Structured suggestions parsed via Function Calling.
        """
        pass

    @abstractmethod
    async def match(self, messages: List[BaseMessage]) -> MatchResult:
        """
        Match resume against JD and return structured score.

        Args:
            messages: Formatted prompt messages from PromptBuilder.

        Returns:
            MatchResult: Score, breakdown, and suggestions via Function Calling.
        """
        pass

    @abstractmethod
    async def optimize(self, messages: List[BaseMessage]) -> LLMResponse:
        """
        Optimize resume and return improved Markdown content.

        Args:
            messages: Formatted prompt messages from PromptBuilder.

        Returns:
            LLMResponse: Free-text Markdown for PDF rendering.
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider identifier string."""
        pass
