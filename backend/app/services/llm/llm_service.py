"""
LLM Service - Middle layer between API endpoints and LangChain chains

Uses LCEL (LangChain Expression Language) with with_structured_output() for
analyze and match operations, eliminating manual JSON parsing. The optimize
operation retains free-text output because its result is Markdown fed directly
into the PDF renderer.
"""

import logging
import re
from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.exceptions import OutputParserException

from app.core.config import settings
from .schemas import (
    AnalyzeResult,
    MatchResult,
    OptimizeResult,
)
from .exceptions import (
    LLMException,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMResponseError,
    LLMServiceUnavailableError,
)
from app.services.validators.content_moderator import (
    get_content_moderator,
    ContentModerationError,
)

logger = logging.getLogger(__name__)

_WEIGHTED_SKILLS     = 0.35
_WEIGHTED_EXPERIENCE = 0.25
_WEIGHTED_EDUCATION  = 0.15
_WEIGHTED_KEYWORDS   = 0.25


def _map_exception(exc: Exception) -> LLMException:
    """Map a generic / LangChain exception to the appropriate custom LLMException."""
    msg = str(exc).lower()
    if "api key" in msg or "unauthenticated" in msg or "permission" in msg:
        return LLMAuthenticationError()
    if "quota" in msg or "rate" in msg or "resource exhausted" in msg:
        return LLMRateLimitError()
    if "unavailable" in msg or "service" in msg or "timeout" in msg or "deadline" in msg:
        return LLMServiceUnavailableError()
    return LLMException(str(exc))


class LLMService:
    """
    LLM Service — orchestrates LangChain chains for the three resume operations.

    analyze / match: use with_structured_output(PydanticModel) so Gemini returns
    data via Function Calling, which LangChain deserialises directly into the
    Pydantic schema — no regex or JSON parsing needed.

    optimize: uses plain ainvoke and returns free-form Markdown text, which is
    cleaned and fed into the PDF renderer.
    """

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY is not set. LLM features will not work.")
            self._analyze_chain = None
            self._match_chain = None
            self._optimize_llm = None
            return

        base_llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=settings.GEMINI_TEMPERATURE,
            max_output_tokens=settings.GEMINI_MAX_TOKENS,
        )

        # match scoring needs low temperature for consistent, reproducible scores
        match_llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.2,
            max_output_tokens=settings.GEMINI_MAX_TOKENS,
        )

        # with_structured_output must be called on the base LLM before with_retry,
        # because RunnableRetry does not expose with_structured_output.
        self._analyze_chain = base_llm.with_structured_output(AnalyzeResult).with_retry(
            stop_after_attempt=settings.GEMINI_MAX_RETRIES
        )
        self._match_chain = match_llm.with_structured_output(MatchResult).with_retry(
            stop_after_attempt=settings.GEMINI_MAX_RETRIES
        )
        self._optimize_llm = base_llm.with_retry(stop_after_attempt=settings.GEMINI_MAX_RETRIES)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def analyze_resume(self, prompt: str) -> AnalyzeResult:
        """Analyze resume and return structured suggestions via Function Calling."""
        if not self._analyze_chain:
            raise LLMServiceUnavailableError("GEMINI_API_KEY not configured")
        try:
            result: AnalyzeResult = await self._analyze_chain.ainvoke(
                [HumanMessage(content=prompt)]
            )
        except OutputParserException as exc:
            logger.error(f"Structured output parsing failed (analyze): {exc}")
            raise LLMResponseError(str(exc))
        except Exception as exc:
            logger.error(f"LLM analyze error: {exc}")
            raise _map_exception(exc)

        moderator = get_content_moderator()
        check_text = " ".join(
            f"{s.title} {s.description}" for s in result.suggestions
        )
        is_safe, reason = moderator.check_output(check_text)
        if not is_safe:
            logger.warning(f"LLM analyze output blocked: {reason}")
            raise ContentModerationError(reason)

        return result

    async def match_resume(self, prompt: str) -> MatchResult:
        """Match resume with JD and return score with suggestions via Function Calling."""
        if not self._match_chain:
            raise LLMServiceUnavailableError("GEMINI_API_KEY not configured")
        try:
            result: MatchResult = await self._match_chain.ainvoke(
                [HumanMessage(content=prompt)]
            )
        except OutputParserException as exc:
            logger.error(f"Structured output parsing failed (match): {exc}")
            raise LLMResponseError(str(exc))
        except Exception as exc:
            logger.error(f"LLM match error: {exc}")
            raise _map_exception(exc)

        # Business rule: overall score must be close to the weighted average of
        # breakdown scores. Deviations > 15 points indicate LLM inflation.
        bd = result.match_breakdown
        expected = round(
            bd.skills_match      * _WEIGHTED_SKILLS
            + bd.experience_match  * _WEIGHTED_EXPERIENCE
            + bd.education_match   * _WEIGHTED_EDUCATION
            + bd.keywords_match    * _WEIGHTED_KEYWORDS
        )
        if abs(result.match_score - expected) > 15:
            logger.warning(
                f"Match score deviation: LLM returned {result.match_score}, "
                f"weighted average is {expected}. Using weighted average."
            )
            result.match_score = expected

        moderator = get_content_moderator()
        check_text = " ".join(
            f"{s.title} {s.description}" for s in result.suggestions
        )
        is_safe, reason = moderator.check_output(check_text)
        if not is_safe:
            logger.warning(f"LLM match output blocked: {reason}")
            raise ContentModerationError(reason)

        return result

    async def optimize_resume(self, prompt: str) -> OptimizeResult:
        """Optimize resume and return improved Markdown content (free-text output)."""
        if not self._optimize_llm:
            raise LLMServiceUnavailableError("GEMINI_API_KEY not configured")
        try:
            response = await self._optimize_llm.ainvoke([HumanMessage(content=prompt)])
            content: str = response.content
        except Exception as exc:
            logger.error(f"LLM optimize error: {exc}")
            raise _map_exception(exc)

        moderator = get_content_moderator()
        is_safe, reason = moderator.check_output(content)
        if not is_safe:
            logger.warning(f"LLM optimize output blocked: {reason}")
            raise ContentModerationError(reason)

        cleaned = self._clean_optimize_output(content)
        return OptimizeResult(optimized_content=cleaned)

    # ------------------------------------------------------------------
    # Output cleaning (optimize only — free-text path)
    # ------------------------------------------------------------------

    # Patterns for non-resume editorial/meta content that LLM may inject.
    _EDITORIAL_PATTERNS = re.compile(
        r'('
        r'\bbug\s+found\b|\bissue\s+found\b|\berror\s+found\b|'
        r'(?:^|\s)note\s*:\s|(?:^|\s)warning\s*:\s|(?:^|\s)todo\s*:\s|(?:^|\s)fixme\s*:\s|'
        r'(?:^|\s)feedback\s*:\s|(?:^|\s)observation\s*:\s|(?:^|\s)comment\s*:\s|'
        r'\bimprovement\s+needed\b|\bneeds\s+improvement\b|\baction\s+required\b|'
        r'\b(?:as\s+an?\s+AI|as\s+a\s+language\s+model|I\s+(?:have|cannot|can\'t)\s+)\b|'
        r'\b(?:this\s+resume\s+(?:needs|lacks|should|could)|the\s+candidate\s+should)\b'
        r')',
        re.IGNORECASE,
    )

    # Patterns that indicate the LLM refused the request or included a safety
    # disclaimer. If these appear the entire output is rejected.
    _LLM_REFUSAL_PATTERNS = re.compile(
        r'('
        r'\bI\s+am\s+sorry\b.*\b(violat|cannot|can\'t|unable|refuse|inappropriate|safety\s+guideline)|'
        r'\bI\s+cannot\s+(fulfill|comply|complete|process|generate)\b|'
        r'\bI\s+can\'t\s+(fulfill|comply|complete|process|generate)\b|'
        r'\bI\'m\s+unable\s+to\b|'
        r'\bviolat\w*\s+(my|the|our)\s+(safety|content|usage)\s+(guideline|polic|rule)|'
        r'\bagainst\s+(my|the|our)\s+(safety|content|usage)\s+(guideline|polic|rule)|'
        r'\b(safety|content)\s+guidelines?\s+(prevent|prohibit|restrict|do\s+not\s+allow)|'
        r'\bapologi[zs]e\b.*\b(cannot|can\'t|unable|inappropriate)|'
        r'\bfulfill\s+(the\s+)?user\'?s?\s+request\b'
        r')',
        re.IGNORECASE,
    )

    def _clean_optimize_output(self, content: str) -> str:
        """
        Remove non-resume artifacts from the LLM's free-text optimize output.

        Raises ContentModerationError if the output contains a refusal or
        safety disclaimer so the frontend receives a clear error.
        """
        if not content or not content.strip():
            return content

        refusal_match = self._LLM_REFUSAL_PATTERNS.search(content)
        if refusal_match:
            logger.warning(
                f"LLM output contains refusal/disclaimer: '{refusal_match.group()[:100]}'"
            )
            raise ContentModerationError(
                "Your input contained content that could not be processed. "
                "Please revise your resume or job description and try again."
            )

        lines = content.split("\n")
        cleaned_lines = []

        for line in lines:
            stripped = line.strip()

            if not stripped:
                cleaned_lines.append(line)
                continue

            if self._EDITORIAL_PATTERNS.search(stripped):
                if stripped.startswith("#"):
                    cleaned = self._EDITORIAL_PATTERNS.sub("", stripped).strip()
                    cleaned = re.sub(
                        r"^\s*#+\s*[-–—:]\s*",
                        lambda m: (
                            m.group().split("-")[0]
                            .split("–")[0]
                            .split("—")[0]
                            .split(":")[0]
                        ),
                        cleaned,
                    )
                    cleaned = re.sub(r"\s*[-–—]\s*$", "", cleaned)
                    if cleaned.strip("#").strip():
                        logger.info(f"Cleaned heading artifact: '{stripped}' -> '{cleaned}'")
                        cleaned_lines.append(cleaned)
                else:
                    cleaned = self._EDITORIAL_PATTERNS.sub("", stripped).strip()
                    cleaned = re.sub(r"^[-*]\s*$", "", cleaned).strip()
                    if cleaned:
                        logger.info(f"Cleaned body artifact: '{stripped}' -> '{cleaned}'")
                        cleaned_lines.append(cleaned)
                    else:
                        logger.info(f"Removed editorial line: '{stripped}'")
            else:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines)


@lru_cache
def get_llm_service() -> LLMService:
    """Get cached LLM service instance (singleton pattern)."""
    return LLMService()
