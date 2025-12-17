"""
LLM Provider Abstract Base Class
Defines the interface that all LLM Providers must implement
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class LLMResponse:
    """LLM response data class"""

    content: str
    model: str
    usage: Optional[dict] = None


@dataclass
class MatchScoreResult:
    """Match score result data class"""

    score: float  # 0.0 - 1.0
    explanation: str
    suggestions: List[str]


class BaseLLMProvider(ABC):
    """
    LLM Provider Abstract Base Class

    All LLM Provider implementations must inherit from this class and implement:
    - optimize: Resume rewriting and optimization
    - analyze: Analyze resume and generate suggestions
    - match: Semantic comparison for match scoring
    """

    @abstractmethod
    async def optimize(
        self,
        resume_content: str,
        job_description: str,
        instructions: Optional[str] = None,
    ) -> LLMResponse:
        """
        Perform resume rewriting and optimization

        Args:
            resume_content: Original resume content
            job_description: Target job description
            instructions: Optional user instructions for optimization

        Returns:
            LLMResponse: Optimized resume content
        """
        pass

    @abstractmethod
    async def analyze(
        self,
        resume_content: str,
        job_description: str,
    ) -> LLMResponse:
        """
        Analyze resume and generate improvement suggestions

        Args:
            resume_content: Resume content to analyze
            job_description: Target job description

        Returns:
            LLMResponse: Analysis and suggestions
        """
        pass

    @abstractmethod
    async def match(
        self,
        resume_content: str,
        job_description: str,
    ) -> MatchScoreResult:
        """
        Provide semantic comparison for match scoring

        Args:
            resume_content: Resume content
            job_description: Job description to match against

        Returns:
            MatchScoreResult: Score and detailed analysis
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name"""
        pass
