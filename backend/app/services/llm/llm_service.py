"""
LLM Service - Middle layer between API endpoints and LLM Provider
Handles prompt sending and response parsing
"""

import json
import logging
import re
from functools import lru_cache
from typing import Optional

from .factory import get_llm_provider
from .base import BaseLLMProvider
from .schemas import (
    Suggestion,
    AnalyzeResult,
    MatchBreakdown,
    MatchResult,
    OptimizeResult,
)
from app.services.validators.content_moderator import (
    get_content_moderator,
    ContentModerationError,
)

logger = logging.getLogger(__name__)


class LLMService:
    """
    LLM Service class - Middle layer
    """

    def __init__(self, provider: Optional[BaseLLMProvider] = None):
        """Initialize LLM service with provider from factory"""
        self.provider = provider or get_llm_provider()

    async def analyze_resume(self, prompt: str) -> AnalyzeResult:
        """Analyze resume and return structured suggestions"""
        response = await self.provider.analyze(prompt, "")  # Pass empty string for job_description
        
        # RA-62: Check output content safety
        moderator = get_content_moderator()
        is_safe, reason = moderator.check_output(response.content)
        if not is_safe:
            logger.warning(f"LLM analyze output blocked: {reason}")
            raise ContentModerationError(reason)

        # Parse response into structured format
        suggestions = self._parse_suggestions(response.content, include_example=True)
        return AnalyzeResult(suggestions=suggestions)

    async def match_resume(self, prompt: str) -> MatchResult:
        """Match resume with JD and return score with suggestions"""
        response = await self.provider.match(prompt, "")  # Pass empty string for job_description
        
        # RA-62: Check output content safety
        moderator = get_content_moderator()
        is_safe, reason = moderator.check_output(response.explanation)
        if not is_safe:
            logger.warning(f"LLM match output blocked: {reason}")
            raise ContentModerationError(reason)

        # Parse response into structured format
        match_score, breakdown = self._parse_match_score(response.explanation)
        suggestions = self._parse_suggestions(response.explanation, include_action=True)

        return MatchResult(
            match_score=match_score,
            match_breakdown=breakdown,
            suggestions=suggestions,
        )

    async def optimize_resume(self, prompt: str) -> OptimizeResult:
        """Optimize resume and return improved content"""
        response = await self.provider.optimize(prompt, "", None)  # Pass empty strings

        # RA-62: Check output content safety
        moderator = get_content_moderator()
        is_safe, reason = moderator.check_output(response.content)
        if not is_safe:
            logger.warning(f"LLM optimize output blocked: {reason}")
            raise ContentModerationError(reason)

        # RA-62: Clean LLM output artifacts
        cleaned_content = self._clean_optimize_output(response.content)

        return OptimizeResult(optimized_content=cleaned_content)

    def _parse_suggestions(
        self,
        content: str,
        include_example: bool = False,
        include_action: bool = False,
    ) -> list[Suggestion]:
        """Parse LLM response content to extract suggestions"""
        json_data = self._extract_json(content)
        if json_data:
            return self._parse_suggestions_from_json(json_data, include_example, include_action)

        # Fallback: parse as structured text (very basic)
        return self._parse_suggestions_from_text(content, include_example, include_action)

    def _extract_json(self, content: str) -> Optional[dict]:
        """Extract JSON object or array from content"""
        # Try markdown blocks
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from markdown block: {e}")
                logger.debug(f"Content: {json_match.group(1)[:500]}...")

        # Try raw JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try to find { ... }
        match = re.search(r"\{[\s\S]*\}", content)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse extracted JSON: {e}")
                logger.debug(f"Extracted JSON preview: {match.group()[:500]}...")
                # Check if JSON appears truncated
                if not match.group().rstrip().endswith('}'):
                    logger.error("JSON appears truncated - response likely cut off due to token limit")
        return None

    def _parse_suggestions_from_json(
        self,
        data: dict,
        include_example: bool,
        include_action: bool,
    ) -> list[Suggestion]:
        """Parse suggestions from JSON data"""
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("suggestions", [])

        suggestions = []
        for item in items:
            if not isinstance(item, dict):
                continue
            
            s = Suggestion(
                category=str(item.get("category", "general")),
                priority=str(item.get("priority", "medium")),
                title=str(item.get("title", "Suggestion")),
                description=str(item.get("description", "")),
            )
            if include_example:
                s.example = str(item.get("example", "N/A"))
            if include_action:
                s.action = str(item.get("action", "N/A"))
            
            suggestions.append(s)
        return suggestions

    def _parse_suggestions_from_text(self, content: str, include_example: bool, include_action: bool) -> list[Suggestion]:
        """Very basic fallback text parser"""
        # Just create one generic suggestion from raw text if parsing fails
        return [Suggestion(
            category="general",
            priority="medium",
            title="Analysis Result",
            description=content[:500],
            example="N/A" if include_example else None,
            action="N/A" if include_action else None
        )]

    # Patterns for non-resume editorial/meta content that LLM may inject.
    # Used by _clean_optimize_output to detect and remove artifacts.
    # These match standalone phrases that would never appear in a real resume.
    _EDITORIAL_PATTERNS = re.compile(
        r'('
        # Status/issue markers injected by LLM
        r'\bbug\s+found\b|\bissue\s+found\b|\berror\s+found\b|'
        # Editorial labels (standalone, not part of job descriptions like "bug reporting")
        r'(?:^|\s)note\s*:\s|(?:^|\s)warning\s*:\s|(?:^|\s)todo\s*:\s|(?:^|\s)fixme\s*:\s|'
        # Feedback/commentary that doesn't belong in a resume
        r'(?:^|\s)feedback\s*:\s|(?:^|\s)observation\s*:\s|(?:^|\s)comment\s*:\s|'
        # Improvement markers (belong in analysis output, not in resume)
        r'\bimprovement\s+needed\b|\bneeds\s+improvement\b|\baction\s+required\b|'
        # LLM self-referencing phrases
        r'\b(?:as\s+an?\s+AI|as\s+a\s+language\s+model|I\s+(?:have|cannot|can\'t)\s+)\b|'
        # Meta-commentary about the resume itself
        r'\b(?:this\s+resume\s+(?:needs|lacks|should|could)|the\s+candidate\s+should)\b'
        r')',
        re.IGNORECASE
    )

    # Patterns that indicate the LLM refused the request or included a safety
    # disclaimer in its output. If these appear, the entire output should be
    # rejected rather than displayed as resume content.
    _LLM_REFUSAL_PATTERNS = re.compile(
        r'('
        # Direct refusal statements
        r'\bI\s+am\s+sorry\b.*\b(violat|cannot|can\'t|unable|refuse|inappropriate|safety\s+guideline)|'
        r'\bI\s+cannot\s+(fulfill|comply|complete|process|generate)\b|'
        r'\bI\s+can\'t\s+(fulfill|comply|complete|process|generate)\b|'
        r'\bI\'m\s+unable\s+to\b|'
        # Safety/policy disclaimers
        r'\bviolat\w*\s+(my|the|our)\s+(safety|content|usage)\s+(guideline|polic|rule)|'
        r'\bagainst\s+(my|the|our)\s+(safety|content|usage)\s+(guideline|polic|rule)|'
        r'\b(safety|content)\s+guidelines?\s+(prevent|prohibit|restrict|do\s+not\s+allow)|'
        # Apology + refusal combo
        r'\bapologi[zs]e\b.*\b(cannot|can\'t|unable|inappropriate)|'
        r'\bfulfill\s+(the\s+)?user\'?s?\s+request\b'
        r')',
        re.IGNORECASE
    )

    def _clean_optimize_output(self, content: str) -> str:
        """
        Clean LLM optimize output by removing non-resume artifacts.

        LLM sometimes injects editorial comments, meta-observations, or
        injected text (from prompt injection via JD) into the optimized
        resume output. This method scans ALL lines and removes content
        that would not belong in a real professional resume.

        If the LLM output contains a refusal or safety disclaimer (e.g.,
        "I am sorry, I cannot fulfill this request..."), the entire output
        is rejected by raising ContentModerationError, so the frontend
        receives a clear error instead of seeing the refusal text as
        resume content.

        Strategy:
        1. First check if the LLM refused the request entirely — if so,
           raise an error immediately.
        2. For heading lines (#): strip any detected editorial phrase
           from the line while preserving the rest.
        3. For body lines: remove entire lines that are purely editorial.
        4. For mixed content: strip only the artifact portion.
        """
        if not content or not content.strip():
            return content

        # Check if LLM refused the request or included safety disclaimers.
        # This means the input likely contained inappropriate content that
        # bypassed our input checks but was caught by the LLM's own safety.
        refusal_match = self._LLM_REFUSAL_PATTERNS.search(content)
        if refusal_match:
            logger.warning(
                f"LLM output contains refusal/disclaimer: '{refusal_match.group()[:100]}'"
            )
            raise ContentModerationError(
                "Your input contained content that could not be processed. "
                "Please revise your resume or job description and try again."
            )

        lines = content.split('\n')
        cleaned_lines = []

        for line in lines:
            stripped = line.strip()

            if not stripped:
                # Preserve blank lines for formatting
                cleaned_lines.append(line)
                continue

            if self._EDITORIAL_PATTERNS.search(stripped):
                if stripped.startswith('#'):
                    # Heading line: remove the editorial phrase, keep the rest
                    cleaned = self._EDITORIAL_PATTERNS.sub('', stripped).strip()
                    # Clean up leftover separators like " - " or " : "
                    cleaned = re.sub(r'^\s*#+\s*[-–—:]\s*', lambda m: m.group().split('-')[0].split('–')[0].split('—')[0].split(':')[0], cleaned)
                    cleaned = re.sub(r'\s*[-–—]\s*$', '', cleaned)
                    if cleaned.strip('#').strip():
                        logger.info(
                            f"Cleaned heading artifact: '{stripped}' -> '{cleaned}'"
                        )
                        cleaned_lines.append(cleaned)
                    # else: heading is entirely editorial, skip it
                else:
                    # Body line: check if the entire line is editorial
                    cleaned = self._EDITORIAL_PATTERNS.sub('', stripped).strip()
                    # Remove leftover bullet markers or separators
                    cleaned = re.sub(r'^[-*]\s*$', '', cleaned).strip()
                    if cleaned:
                        # Line has real content mixed in, keep the cleaned version
                        logger.info(
                            f"Cleaned body artifact: '{stripped}' -> '{cleaned}'"
                        )
                        cleaned_lines.append(cleaned)
                    else:
                        # Entire line was editorial, remove it
                        logger.info(
                            f"Removed editorial line: '{stripped}'"
                        )
            else:
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def _parse_match_score(self, content: str) -> tuple[int, MatchBreakdown]:
        """
        Parse match score and breakdown from LLM response.

        Includes reasonability checks:
        - All scores are clamped to 0-100 range.
        - The overall match_score is validated against the weighted average
          of breakdown scores. If they deviate significantly, the weighted
          average is used instead (prevents LLM from inflating the total).
        """
        json_data = self._extract_json(content)
        breakdown = MatchBreakdown()
        score = 0

        if json_data and isinstance(json_data, dict):
            # Clamp all scores to 0-100
            score = max(0, min(100, int(json_data.get("match_score", 0))))
            bd = json_data.get("match_breakdown", {})
            breakdown = MatchBreakdown(
                skills_match=max(0, min(100, int(bd.get("skills_match", 0)))),
                experience_match=max(0, min(100, int(bd.get("experience_match", 0)))),
                education_match=max(0, min(100, int(bd.get("education_match", 0)))),
                keywords_match=max(0, min(100, int(bd.get("keywords_match", 0)))),
            )

            # Validate: overall score should be close to weighted average
            # Weights: skills 35%, experience 25%, education 15%, keywords 25%
            expected_score = round(
                breakdown.skills_match * 0.35
                + breakdown.experience_match * 0.25
                + breakdown.education_match * 0.15
                + breakdown.keywords_match * 0.25
            )

            if abs(score - expected_score) > 15:
                logger.warning(
                    f"Match score deviation: LLM returned {score}, "
                    f"weighted average is {expected_score}. "
                    f"Using weighted average."
                )
                score = expected_score

        return score, breakdown


@lru_cache
def get_llm_service() -> LLMService:
    """Get cached LLM service instance (singleton pattern)"""
    return LLMService()
