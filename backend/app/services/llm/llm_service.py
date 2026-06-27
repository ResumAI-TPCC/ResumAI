"""
LLM Service - Middle layer between API routes and the LLM provider.

Responsibilities:
  - Call provider.analyze / match / optimize with the messages assembled
    by PromptBuilder (List[BaseMessage]).
  - Apply business rules that live above the LLM layer:
      * Content moderation on LLM output (RA-62)
      * Match score deviation correction (weighted-average guard-rail)
      * Optimize output artifact cleaning
  - Map provider errors to HTTP-friendly LLMException subclasses.

What this layer does NOT do (handled by GeminiProvider):
  - JSON parsing / structured output — replaced by with_structured_output()
  - Retry logic — replaced by with_retry()
  - Low-level API error handling
"""

import logging
import re
from functools import lru_cache
from typing import List, Optional

from langchain_core.messages import BaseMessage

from .factory import get_llm_provider
from .base import BaseLLMProvider
from .schemas import (
    AnalyzeResult,
    MatchResult,
    OptimizeResult,
)
from .exceptions import LLMException
from app.services.validators.content_moderator import (
    get_content_moderator,
    ContentModerationError,
)

logger = logging.getLogger(__name__)

_WEIGHTED_SKILLS     = 0.35
_WEIGHTED_EXPERIENCE = 0.25
_WEIGHTED_EDUCATION  = 0.15
_WEIGHTED_KEYWORDS   = 0.25


class LLMService:
    """
    LLM Service — orchestrates provider calls and applies business logic.
    """

    def __init__(self, provider: Optional[BaseLLMProvider] = None):
        self.provider = provider or get_llm_provider()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def analyze_resume(self, messages: List[BaseMessage]) -> AnalyzeResult:
        """Analyze resume and return structured suggestions."""
        try:
            result: AnalyzeResult = await self.provider.analyze(messages)
        except LLMException:
            raise
        except Exception as exc:
            logger.error(f"Unexpected error in analyze_resume: {exc}")
            raise LLMException(str(exc)) from exc

        moderator = get_content_moderator()
        check_text = " ".join(
            f"{s.title} {s.description}" for s in result.suggestions
        )
        is_safe, reason = moderator.check_output(check_text)
        if not is_safe:
            logger.warning(f"LLM analyze output blocked: {reason}")
            raise ContentModerationError(reason)

        return result

    async def match_resume(self, messages: List[BaseMessage]) -> MatchResult:
        """Match resume with JD and return score with suggestions."""
        try:
            result: MatchResult = await self.provider.match(messages)
        except LLMException:
            raise
        except Exception as exc:
            logger.error(f"Unexpected error in match_resume: {exc}")
            raise LLMException(str(exc)) from exc

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
            f"{s.title} {s.description} {s.action or ''}" for s in result.suggestions
        )
        is_safe, reason = moderator.check_output(check_text)
        if not is_safe:
            logger.warning(f"LLM match output blocked: {reason}")
            raise ContentModerationError(reason)

        return result

    async def optimize_resume(self, messages: List[BaseMessage]) -> OptimizeResult:
        """Optimize resume and return cleaned Markdown content."""
        try:
            response = await self.provider.optimize(messages)
        except LLMException:
            raise
        except Exception as exc:
            logger.error(f"Unexpected error in optimize_resume: {exc}")
            raise LLMException(str(exc)) from exc

        moderator = get_content_moderator()
        is_safe, reason = moderator.check_output(response.content)
        if not is_safe:
            logger.warning(f"LLM optimize output blocked: {reason}")
            raise ContentModerationError(reason)

        cleaned = self._clean_optimize_output(response.content)
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
                f"LLM output contains refusal/disclaimer: "
                f"'{refusal_match.group()[:100]}'"
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
                        logger.info(
                            f"Cleaned heading artifact: '{stripped}' -> '{cleaned}'"
                        )
                        cleaned_lines.append(cleaned)
                else:
                    cleaned = self._EDITORIAL_PATTERNS.sub("", stripped).strip()
                    cleaned = re.sub(r"^[-*]\s*$", "", cleaned).strip()
                    if cleaned:
                        logger.info(
                            f"Cleaned body artifact: '{stripped}' -> '{cleaned}'"
                        )
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
