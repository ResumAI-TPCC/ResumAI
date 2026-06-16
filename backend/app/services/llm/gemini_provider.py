"""
Google Gemini LLM Provider — LangChain-based implementation.

Replaces the direct google-genai SDK with langchain-google-genai so that:
  - with_structured_output() drives schema enforcement via Function Calling
    for analyze and match, eliminating all manual JSON parsing.
  - with_retry() replaces the hand-written retry loop with exponential backoff.
  - Messages assembled by PromptBuilder (List[BaseMessage]) are passed
    directly to ainvoke(), keeping the provider interface clean.

optimize uses plain ainvoke() because its result is free-text Markdown
fed into the PDF renderer — no structured output is needed.
"""

import logging
from typing import List, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage
from langchain_core.exceptions import OutputParserException

from app.core.config import settings

from .base import BaseLLMProvider, LLMResponse
from .schemas import AnalyzeResult, MatchResult
from .exceptions import (
    LLMException,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMResponseError,
    LLMServiceUnavailableError,
)

logger = logging.getLogger(__name__)


def _map_exception(exc: Exception) -> LLMException:
    """Map a generic / LangChain exception to the appropriate LLMException."""
    msg = str(exc).lower()
    if "api key" in msg or "unauthenticated" in msg or "permission" in msg:
        return LLMAuthenticationError()
    if "quota" in msg or "rate" in msg or "resource exhausted" in msg:
        return LLMRateLimitError()
    if "unavailable" in msg or "service" in msg or "timeout" in msg or "deadline" in msg:
        return LLMServiceUnavailableError()
    return LLMException(str(exc))


class GeminiProvider(BaseLLMProvider):
    """
    LangChain-backed Gemini provider.

    Chain construction (in __init__):
      _analyze_chain  = ChatGoogleGenerativeAI.with_structured_output(AnalyzeResult)
                          .with_retry(...)
      _match_chain    = ChatGoogleGenerativeAI(temp=0.2)
                          .with_structured_output(MatchResult)
                          .with_retry(...)
      _optimize_llm   = ChatGoogleGenerativeAI.with_retry(...)

    All three accept List[BaseMessage] via .ainvoke(messages).
    """

    def __init__(self, api_key: Optional[str] = None):
        resolved_key = api_key or settings.GEMINI_API_KEY

        if not resolved_key:
            logger.warning("GEMINI_API_KEY is not set. LLM features will not work.")
            self._analyze_chain = None
            self._match_chain = None
            self._optimize_llm = None
            return

        base_llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=resolved_key,
            temperature=settings.GEMINI_TEMPERATURE,
            max_output_tokens=settings.GEMINI_MAX_TOKENS,
        )

        # match scoring uses low temperature for consistent, reproducible scores
        match_llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=resolved_key,
            temperature=0.2,
            max_output_tokens=settings.GEMINI_MAX_TOKENS,
        )

        # with_structured_output must be called on the bare LLM before with_retry
        # because RunnableRetry does not expose with_structured_output.
        self._analyze_chain = base_llm.with_structured_output(AnalyzeResult).with_retry(
            stop_after_attempt=settings.GEMINI_MAX_RETRIES
        )
        self._match_chain = match_llm.with_structured_output(MatchResult).with_retry(
            stop_after_attempt=settings.GEMINI_MAX_RETRIES
        )
        self._optimize_llm = base_llm.with_retry(
            stop_after_attempt=settings.GEMINI_MAX_RETRIES
        )

    @property
    def provider_name(self) -> str:
        return "gemini"

    async def analyze(self, messages: List[BaseMessage]) -> AnalyzeResult:
        """
        Analyze resume via Function Calling and return structured suggestions.

        Args:
            messages: [SystemMessage, HumanMessage] from PromptBuilder.

        Returns:
            AnalyzeResult: Pydantic model populated by LangChain structured output.
        """
        if not self._analyze_chain:
            raise LLMAuthenticationError("Gemini API key not configured")
        try:
            result: AnalyzeResult = await self._analyze_chain.ainvoke(messages)
            logger.debug(
                f"analyze: received {len(result.suggestions)} suggestion(s)"
            )
            return result
        except OutputParserException as exc:
            logger.error(f"Structured output parsing failed (analyze): {exc}")
            raise LLMResponseError(str(exc))
        except Exception as exc:
            logger.error(f"Gemini analyze error: {exc}")
            raise _map_exception(exc)

    async def match(self, messages: List[BaseMessage]) -> MatchResult:
        """
        Match resume against JD via Function Calling and return structured score.

        Args:
            messages: [SystemMessage, HumanMessage] from PromptBuilder.

        Returns:
            MatchResult: Pydantic model with score, breakdown, suggestions.
        """
        if not self._match_chain:
            raise LLMAuthenticationError("Gemini API key not configured")
        try:
            result: MatchResult = await self._match_chain.ainvoke(messages)
            logger.debug(
                f"match: score={result.match_score}, "
                f"suggestions={len(result.suggestions)}"
            )
            return result
        except OutputParserException as exc:
            logger.error(f"Structured output parsing failed (match): {exc}")
            raise LLMResponseError(str(exc))
        except Exception as exc:
            logger.error(f"Gemini match error: {exc}")
            raise _map_exception(exc)

    async def optimize(self, messages: List[BaseMessage]) -> LLMResponse:
        """
        Optimize resume and return free-text Markdown content.

        Args:
            messages: [SystemMessage, HumanMessage] from PromptBuilder.

        Returns:
            LLMResponse: Raw Markdown string for downstream cleaning and PDF render.
        """
        if not self._optimize_llm:
            raise LLMAuthenticationError("Gemini API key not configured")
        try:
            response = await self._optimize_llm.ainvoke(messages)
            content: str = response.content
            logger.debug(f"optimize: received {len(content)} chars")
            return LLMResponse(content=content, model=settings.GEMINI_MODEL)
        except Exception as exc:
            logger.error(f"Gemini optimize error: {exc}")
            raise _map_exception(exc)
