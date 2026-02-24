"""
Google Gemini LLM Provider Implementation
Uses the official google-genai SDK to interact with Gemini API
"""

import asyncio
import logging
from typing import Optional, Dict, Any

from google import genai
from google.genai import types

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
    Google Gemini LLM Provider (using google-genai SDK)

    Responsibilities:
    - Receive prompts from upstream services
    - Send requests to Gemini API via official SDK
    - Handle errors (timeout, rate limiting, authentication failures, etc.)
    - Parse responses and return structured results
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini provider with settings from config"""
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL
        self.temperature = settings.GEMINI_TEMPERATURE
        self.max_tokens = settings.GEMINI_MAX_TOKENS
        self.timeout = settings.GEMINI_TIMEOUT
        self.max_retries = settings.GEMINI_MAX_RETRIES
        self.retry_delay = settings.GEMINI_RETRY_DELAY

        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set. LLM features will not work.")

        # Initialize the genai client
        self.client = genai.Client(api_key=self.api_key)

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
        Send prompt to Gemini API and return raw response data

        Args:
            prompt: The prompt to send
            model: Optional model override
            temperature: Optional temperature override
            max_tokens: Optional max_tokens override

        Returns:
            dict: Parsed response data with 'candidates' structure

        Raises:
            LLMAuthenticationError: Invalid API key
            LLMRateLimitError: Rate limit exceeded
            LLMTimeoutError: Request timeout
            LLMResponseError: Failed to parse response
            LLMServiceUnavailableError: Service unavailable
        """
        use_model = model or self.model
        use_temperature = temperature if temperature is not None else self.temperature
        use_max_tokens = max_tokens or self.max_tokens

        config = types.GenerateContentConfig(
            temperature=use_temperature,
            max_output_tokens=use_max_tokens,
        )

        # Make request with retry logic
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                return await self._make_request(prompt, use_model, config)

            except LLMRateLimitError as e:
                last_exception = e
                wait_time = self.retry_delay * (2 ** attempt)
                logger.warning(
                    f"Rate limited, retrying in {wait_time}s "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
                await asyncio.sleep(wait_time)

            except LLMTimeoutError as e:
                last_exception = e
                logger.warning(
                    f"Request timeout, retrying "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )

            except (LLMAuthenticationError, LLMResponseError):
                raise

        raise last_exception or LLMException("All retry attempts failed")

    async def _make_request(
        self, prompt: str, model: str, config: types.GenerateContentConfig
    ) -> Dict[str, Any]:
        """Send request to Gemini API via genai SDK"""
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.models.generate_content,
                    model=model,
                    contents=prompt,
                    config=config,
                ),
                timeout=self.timeout,
            )

            # Convert SDK response to dict format for backward compatibility
            return self._response_to_dict(response)

        except asyncio.TimeoutError:
            logger.error("Gemini API request timeout")
            raise LLMTimeoutError()

        except Exception as e:
            error_msg = str(e).lower()
            if "api key" in error_msg or "401" in error_msg or "403" in error_msg:
                raise LLMAuthenticationError(str(e))
            if "429" in error_msg or "rate" in error_msg:
                raise LLMRateLimitError(str(e))
            if "500" in error_msg or "503" in error_msg or "unavailable" in error_msg:
                raise LLMServiceUnavailableError(str(e))
            logger.error(f"Gemini API error: {e}")
            raise LLMException(f"Gemini API error: {e}")

    def _response_to_dict(self, response) -> Dict[str, Any]:
        """Convert genai SDK response object to dict for backward compatibility"""
        try:
            result = {
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": response.text}]
                        }
                    }
                ]
            }

            # Include usage metadata if available
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                result["usageMetadata"] = {
                    "promptTokenCount": getattr(
                        response.usage_metadata, "prompt_token_count", 0
                    ),
                    "candidatesTokenCount": getattr(
                        response.usage_metadata, "candidates_token_count", 0
                    ),
                    "totalTokenCount": getattr(
                        response.usage_metadata, "total_token_count", 0
                    ),
                }

            return result
        except (AttributeError, TypeError) as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            raise LLMResponseError(f"Invalid response format: {e}")

    def _extract_content(self, data: dict) -> str:
        """Extract content from Gemini API response"""
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Failed to extract content from response: {e}")
            raise LLMResponseError(f"Invalid response format: {e}")

    def _extract_usage(self, data: dict) -> Optional[dict]:
        """Extract usage information from Gemini API response"""
        return data.get("usageMetadata")

    # Implementation of abstract methods from BaseLLMProvider

    async def optimize(
        self,
        resume_content: str,
        job_description: str,
        instructions: Optional[str] = None,
    ) -> LLMResponse:
        """Perform resume rewriting and optimization"""
        prompt = resume_content
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
        """Analyze resume and generate improvement suggestions"""
        prompt = resume_content
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
        """Provide semantic comparison for match scoring"""
        prompt = resume_content
        data = await self.send_prompt(prompt)
        content = self._extract_content(data)
        return MatchScoreResult(
            score=0.0,
            explanation=content,
            suggestions=[],
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
