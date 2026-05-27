"""
Google Gemini LLM Provider Implementation (LangChain-based)

Thin adapter that satisfies the BaseLLMProvider interface using
ChatGoogleGenerativeAI from langchain-google-genai. All prompt
construction and structured output parsing are handled by LLMService;
this class exists to preserve the factory/registration pattern.
"""

import logging
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from app.core.config import settings

from .base import BaseLLMProvider, LLMResponse, MatchScoreResult

logger = logging.getLogger(__name__)

_LOW_TEMP = 0.2


class GeminiProvider(BaseLLMProvider):
    """
    LangChain-backed Gemini Provider.

    Keeps the BaseLLMProvider interface intact so the factory/registry
    pattern continues to work. In practice, LLMService calls LangChain
    chains directly (with structured output); this provider is used only
    when someone calls get_llm_provider() directly.
    """

    def __init__(self, api_key: Optional[str] = None):
        resolved_key = api_key or settings.GEMINI_API_KEY
        if not resolved_key:
            logger.warning("GEMINI_API_KEY is not set. LLM features will not work.")
            self._llm = None
            self._llm_low_temp = None
            return

        self._llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=resolved_key,
            temperature=settings.GEMINI_TEMPERATURE,
            max_output_tokens=settings.GEMINI_MAX_TOKENS,
        ).with_retry(stop_after_attempt=settings.GEMINI_MAX_RETRIES)

        self._llm_low_temp = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=resolved_key,
            temperature=_LOW_TEMP,
            max_output_tokens=settings.GEMINI_MAX_TOKENS,
        ).with_retry(stop_after_attempt=settings.GEMINI_MAX_RETRIES)

    @property
    def provider_name(self) -> str:
        return "gemini"

    async def optimize(
        self,
        resume_content: str,
        job_description: str,
        instructions: Optional[str] = None,
    ) -> LLMResponse:
        if not self._llm:
            raise RuntimeError("Gemini API key not configured")
        response = await self._llm.ainvoke([HumanMessage(content=resume_content)])
        return LLMResponse(content=response.content, model=settings.GEMINI_MODEL)

    async def analyze(
        self,
        resume_content: str,
        job_description: str,
    ) -> LLMResponse:
        if not self._llm:
            raise RuntimeError("Gemini API key not configured")
        response = await self._llm.ainvoke([HumanMessage(content=resume_content)])
        return LLMResponse(content=response.content, model=settings.GEMINI_MODEL)

    async def match(
        self,
        resume_content: str,
        job_description: str,
    ) -> MatchScoreResult:
        if not self._llm_low_temp:
            raise RuntimeError("Gemini API key not configured")
        response = await self._llm_low_temp.ainvoke([HumanMessage(content=resume_content)])
        return MatchScoreResult(
            score=0.0,
            explanation=response.content,
            suggestions=[],
        )
