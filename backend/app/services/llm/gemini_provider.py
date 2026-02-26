"""
Google Gemini LLM Provider Implementation
Sends prompts to Gemini API and handles responses using Google GenAI SDK

Note: Migrated from deprecated google-generativeai to google-genai package.
See: https://github.com/google-gemini/deprecated-generative-ai-python/blob/main/README.md
"""

import asyncio
import logging
from typing import Optional, Dict, Any

from google import genai
from google.genai import types
from google.api_core import exceptions as google_exceptions

from app.core.config import settings

from .base import BaseLLMProvider, LLMResponse, MatchScoreResult
from .exceptions import (
    LLMException,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMResponseError,
    LLMServiceUnavailableError,
)

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini LLM Provider

    Responsibilities:
    - Receive prompts from upstream services
    - Send requests to Gemini API using official Google GenAI SDK
    - Handle errors (timeout, rate limiting, authentication failures, etc.)
    - Parse responses and return structured results
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini provider with settings from config"""
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self.temperature = settings.GEMINI_TEMPERATURE
        self.max_tokens = settings.GEMINI_MAX_TOKENS
        self.timeout = settings.GEMINI_TIMEOUT
        self.max_retries = settings.GEMINI_MAX_RETRIES
        self.retry_delay = settings.GEMINI_RETRY_DELAY

        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set. LLM features will not work.")
            self.client = None
            self.model = None
        else:
            # Initialize the client with API key
            self.client = genai.Client(api_key=self.api_key)
            
            # Store generation config for model calls
            self.generation_config = types.GenerateContentConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            )
    
    @property
    def provider_name(self) -> str:
        """Return provider name"""
        return "gemini"

    async def send_prompt(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> types.GenerateContentResponse:
        """
        Send prompt to Gemini API and return response

        Args:
            prompt: The prompt to send
            model: Optional model override (not used, set at initialization)
            temperature: Optional temperature override
            max_tokens: Optional max_tokens override

        Returns:
            GenerateContentResponse: API response object

        Raises:
            LLMAuthenticationError: Invalid API key
            LLMRateLimitError: Rate limit exceeded
            LLMTimeoutError: Request timeout
            LLMResponseError: Failed to parse response
            LLMServiceUnavailableError: Service unavailable
        """
        if not self.client:
            raise LLMAuthenticationError("Gemini API key not configured")
        
        # Build generation config with overrides
        config = self.generation_config
        if temperature is not None or max_tokens is not None:
            config = types.GenerateContentConfig(
                temperature=temperature if temperature is not None else self.temperature,
                max_output_tokens=max_tokens if max_tokens is not None else self.max_tokens,
            )

        # Make request with retry logic
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                # Use async generate_content
                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config,
                )

                return response

            except google_exceptions.ResourceExhausted as e:
                # Rate limit exceeded
                last_exception = LLMRateLimitError(str(e))
                wait_time = self.retry_delay * (2**attempt)  # Exponential backoff
                logger.warning(
                    f"Rate limited, retrying in {wait_time}s "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
                await asyncio.sleep(wait_time)

            except google_exceptions.DeadlineExceeded as e:
                # Request timeout
                last_exception = LLMTimeoutError(str(e))
                logger.warning(
                    f"Request timeout, retrying "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )

            except (google_exceptions.Unauthenticated, google_exceptions.PermissionDenied) as e:
                # Authentication errors should not be retried
                logger.error(f"Authentication error: {e}")
                raise LLMAuthenticationError(str(e))

            except google_exceptions.InvalidArgument as e:
                # Bad request, don't retry
                logger.error(f"Invalid argument: {e}")
                raise LLMResponseError(str(e))

            except google_exceptions.ServiceUnavailable as e:
                # Service unavailable, retry
                last_exception = LLMServiceUnavailableError(str(e))
                wait_time = self.retry_delay * (2**attempt)
                logger.warning(
                    f"Service unavailable, retrying in {wait_time}s "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
                await asyncio.sleep(wait_time)

            except Exception as e:
                # Unexpected error
                logger.error(f"Unexpected error during Gemini API call: {e}")
                raise LLMException(f"Unexpected error: {e}")

        # All retries exhausted
        raise last_exception or LLMException("All retry attempts failed")

    def _extract_content(self, response: types.GenerateContentResponse) -> str:
        """Extract text content from Gemini response"""
        try:
            return response.text
        except (AttributeError, ValueError) as e:
            logger.error(f"Failed to extract content from response: {e}")
            raise LLMResponseError(f"Invalid response format: {e}")

    def _extract_usage(self, response: types.GenerateContentResponse) -> Optional[dict]:
        """Extract usage information from Gemini response"""
        try:
            if hasattr(response, "usage_metadata"):
                return {
                    "prompt_token_count": response.usage_metadata.prompt_token_count,
                    "candidates_token_count": response.usage_metadata.candidates_token_count,
                    "total_token_count": response.usage_metadata.total_token_count,
                }
        except Exception as e:
            logger.warning(f"Could not extract usage metadata: {e}")
        return None

    # Implementation of abstract methods from BaseLLMProvider

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
        # Note: Prompt construction is handled by upstream service
        # This method receives the complete prompt
        prompt = resume_content  # Upstream should pass the full constructed prompt

        response = await self.send_prompt(prompt)

        return LLMResponse(
            content=self._extract_content(response),
            model=self.model_name,
            usage=self._extract_usage(response),
        )

    async def analyze(
        self,
        resume_content: str,
        job_description: str,
    ) -> LLMResponse:
        """
        Analyze resume and generate improvement suggestions

        Args:
            resume_content: Resume content to analyze (or full prompt from upstream)
            job_description: Target job description

        Returns:
            LLMResponse: Analysis and suggestions
        """
        # Note: Prompt construction is handled by upstream service
        prompt = resume_content  # Upstream should pass the full constructed prompt

        response = await self.send_prompt(prompt)

        return LLMResponse(
            content=self._extract_content(response),
            model=self.model_name,
            usage=self._extract_usage(response),
        )

    async def match(
        self,
        resume_content: str,
        job_description: str,
    ) -> MatchScoreResult:
        """
        Provide semantic comparison for match scoring

        Args:
            resume_content: Resume content (or full prompt from upstream)
            job_description: Job description to match against

        Returns:
            MatchScoreResult: Score and detailed analysis
        """
        # Note: Prompt construction is handled by upstream service
        prompt = resume_content  # Upstream should pass the full constructed prompt

        response = await self.send_prompt(prompt)
        content = self._extract_content(response)

        # Parse the response to extract score and suggestions
        # This is a simplified implementation - actual parsing logic
        # should be handled by upstream or a dedicated parser
        return MatchScoreResult(
            score=0.0,  # To be parsed from content
            explanation=content,
            suggestions=[],  # To be parsed from content
        )


# Convenience function for direct prompt sending
async def send_to_gemini(
    prompt: str,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Convenience function to send prompt to Gemini

    Args:
        prompt: The prompt to send
        model: Optional model override
        temperature: Optional temperature override
        max_tokens: Optional max_tokens override

    Returns:
        str: LLM response content
    """
    provider = GeminiProvider()
    response = await provider.send_prompt(prompt, model, temperature, max_tokens)
    return provider._extract_content(response)
