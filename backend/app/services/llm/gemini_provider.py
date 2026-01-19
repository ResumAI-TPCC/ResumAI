"""
Google Gemini LLM Provider Implementation
Sends prompts to Gemini API and handles responses
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List

import httpx

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
    - Send HTTP requests to Gemini API
    - Handle errors (timeout, rate limiting, authentication failures, etc.)
    - Parse responses and return structured results
    """

    def __init__(self):
        """Initialize Gemini provider with settings from config"""
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model
        self.temperature = settings.gemini_temperature
        self.max_tokens = settings.gemini_max_tokens
        self.timeout = settings.gemini_timeout
        self.max_retries = settings.gemini_max_retries
        self.retry_delay = settings.gemini_retry_delay

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")

        # Construct base URL with model and API key
        self.base_url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
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
    ) -> Dict[str, Any]:
        """
        Send prompt to Gemini API and return raw response

        Args:
            prompt: The prompt to send
            model: Optional model override
            temperature: Optional temperature override
            max_tokens: Optional max_tokens override

        Returns:
            dict: Raw API response data

        Raises:
            LLMAuthenticationError: Invalid API key
            LLMRateLimitError: Rate limit exceeded
            LLMTimeoutError: Request timeout
            LLMResponseError: Failed to parse response
            LLMServiceUnavailableError: Service unavailable
        """
        # Build URL (model might be overridden)
        url = self._build_url(model)
        payload = self._build_payload(prompt, temperature, max_tokens)

        # Make request with retry logic
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                return await self._make_request(url, payload)

            except LLMRateLimitError as e:
                # Wait and retry on rate limit
                last_exception = e
                wait_time = self.retry_delay * (2**attempt)  # Exponential backoff
                logger.warning(
                    f"Rate limited, retrying in {wait_time}s "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
                await asyncio.sleep(wait_time)

            except LLMTimeoutError as e:
                # Retry on timeout
                last_exception = e
                logger.warning(
                    f"Request timeout, retrying "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )

            except (LLMAuthenticationError, LLMResponseError):
                # These errors should not be retried
                raise

        # All retries exhausted
        raise last_exception or LLMException("All retry attempts failed")

    def _build_url(self, model: Optional[str] = None) -> str:
        """Build API URL with model"""
        use_model = model or self.model
        return (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{use_model}:generateContent?key={self.api_key}"
        )

    def _build_payload(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> dict:
        """Build API request payload for Gemini"""
        return {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature
                if temperature is not None
                else self.temperature,
                "maxOutputTokens": max_tokens or self.max_tokens,
            },
        }

    async def _make_request(self, url: str, payload: dict) -> Dict[str, Any]:
        """Send HTTP request to Gemini API"""
        headers = {
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                )

                # Handle HTTP status codes
                self._handle_status_code(response)

                # Return parsed JSON
                return response.json()

        except httpx.TimeoutException:
            logger.error("Gemini API request timeout")
            raise LLMTimeoutError()

        except httpx.ConnectError:
            logger.error("Failed to connect to Gemini API")
            raise LLMServiceUnavailableError("Cannot connect to Gemini service")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code}")
            raise LLMException(f"HTTP error: {e.response.status_code}")

    def _handle_status_code(self, response: httpx.Response) -> None:
        """Handle HTTP status codes"""
        if response.status_code == 200:
            return

        if response.status_code == 400:
            # Check if it's an API key issue
            try:
                error_data = response.json()
                error_message = error_data.get("error", {}).get("message", "")
                if "API key" in error_message:
                    raise LLMAuthenticationError(error_message)
            except (ValueError, KeyError):
                pass
            raise LLMException("Bad request to Gemini API", status_code=400)

        if response.status_code == 401 or response.status_code == 403:
            raise LLMAuthenticationError()

        if response.status_code == 429:
            raise LLMRateLimitError()

        if response.status_code >= 500:
            raise LLMServiceUnavailableError(
                f"Gemini API returned {response.status_code}"
            )

        # Handle other errors
        try:
            error_data = response.json()
            error_message = error_data.get("error", {}).get("message", "Unknown error")
        except Exception:
            error_message = response.text

        raise LLMException(
            f"Gemini API error: {error_message}", status_code=response.status_code
        )

    def _extract_content(self, data: dict) -> str:
        """Extract content from Gemini API response"""
        try:
            # Gemini response structure:
            # { "candidates": [{ "content": { "parts": [{ "text": "..." }] } }] }
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Failed to extract content from response: {e}")
            raise LLMResponseError(f"Invalid response format: {e}")

    def _extract_usage(self, data: dict) -> Optional[dict]:
        """Extract usage information from Gemini API response"""
        # Gemini includes usage in usageMetadata
        return data.get("usageMetadata")

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

        data = await self.send_prompt(prompt)

        return LLMResponse(
            content=self._extract_content(data),
            model=self.model,
            usage=self._extract_usage(data),
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

        data = await self.send_prompt(prompt)

        return LLMResponse(
            content=self._extract_content(data),
            model=self.model,
            usage=self._extract_usage(data),
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

        data = await self.send_prompt(prompt)
        content = self._extract_content(data)

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
    data = await provider.send_prompt(prompt, model, temperature, max_tokens)
    return provider._extract_content(data)
