"""
Google Gemini LLM Provider Implementation
"""

from typing import Optional

import google.generativeai as genai
from starlette.concurrency import run_in_threadpool

from app.core.config import settings

from .base import BaseLLMProvider, LLMResponse, MatchScoreResult


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini API Provider

    Implements the BaseLLMProvider interface for Google's Gemini models.
    """

    def __init__(self):
        """Initialize Gemini client with API key from settings."""
        if not settings.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not configured. "
                "Please set the GEMINI_API_KEY environment variable."
            )
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "gemini"

    async def optimize(
        self,
        resume_content: str,
        job_description: str = "",
        instructions: Optional[str] = None,
    ) -> LLMResponse:
        """
        Optimize resume using Gemini API.

        Args:
            resume_content: Original resume content
            job_description: Target job description (optional for general optimization)
            instructions: Additional user instructions (optional)

        Returns:
            LLMResponse: Optimized resume content in Markdown format
        """
        from app.services.prompt.templates import (
            OPTIMIZE_PROMPT_TEMPLATE,
            OPTIMIZE_WITH_JD_PROMPT_TEMPLATE,
        )

        # Choose template based on whether JD is provided
        if job_description and job_description.strip():
            prompt = OPTIMIZE_WITH_JD_PROMPT_TEMPLATE.format(
                resume_content=resume_content,
                job_description=job_description,
            )
        else:
            prompt = OPTIMIZE_PROMPT_TEMPLATE.format(
                resume_content=resume_content,
            )

        # Add optional user instructions
        if instructions:
            prompt += f"\n\n## Additional Instructions:\n{instructions}"

        # Call Gemini API
        response = await self._generate_content(prompt)

        return LLMResponse(
            content=response.text,
            model=settings.GEMINI_MODEL,
            usage=None,  # Gemini SDK doesn't expose usage in the same way
        )

    async def analyze(
        self,
        resume_content: str,
        job_description: str,
    ) -> LLMResponse:
        """
        Analyze resume and generate improvement suggestions.

        Args:
            resume_content: Resume content to analyze
            job_description: Target job description

        Returns:
            LLMResponse: Analysis and suggestions in JSON format
        """
        from app.services.prompt.templates import ANALYZE_PROMPT_TEMPLATE

        prompt = ANALYZE_PROMPT_TEMPLATE.format(
            resume_content=resume_content,
        )

        response = await self._generate_content(prompt)

        return LLMResponse(
            content=response.text,
            model=settings.GEMINI_MODEL,
            usage=None,
        )

    async def match(
        self,
        resume_content: str,
        job_description: str,
    ) -> MatchScoreResult:
        """
        Calculate match score between resume and job description.

        Args:
            resume_content: Resume content
            job_description: Job description to match against

        Returns:
            MatchScoreResult: Score and detailed analysis

        Note:
            Not implemented yet - placeholder for future implementation
        """
        raise NotImplementedError("Match scoring is not implemented yet")

    async def _generate_content(self, prompt: str):
        """
        Call Gemini API to generate content.

        Uses run_in_threadpool to avoid blocking the event loop
        since the Gemini SDK uses synchronous calls.

        Args:
            prompt: The prompt to send to Gemini

        Returns:
            Gemini API response object
        """
        return await run_in_threadpool(self.model.generate_content, prompt)
