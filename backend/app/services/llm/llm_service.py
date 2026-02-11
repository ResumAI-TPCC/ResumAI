"""
LLM Service - Middle layer between API endpoints and LLM Provider
Handles prompt sending and response parsing
"""

import json
import logging
import re
from typing import Optional

from .gemini_provider import GeminiProvider
from .schemas import (
    Suggestion,
    AnalyzeResult,
    MatchBreakdown,
    MatchResult,
    OptimizeResult,
)

logger = logging.getLogger(__name__)


class LLMService:
    """
    LLM Service class - Middle layer
    """

    def __init__(self, provider: Optional[GeminiProvider] = None):
        """Initialize LLM service with Gemini provider"""
        self.provider = provider or GeminiProvider()

    async def analyze_resume(self, prompt: str) -> AnalyzeResult:
        """Analyze resume and return structured suggestions"""
        data = await self.provider.send_prompt(prompt)
        raw_content = self.provider._extract_content(data)

        # Parse response into structured format
        suggestions = self._parse_suggestions(raw_content, include_example=True)
        return AnalyzeResult(suggestions=suggestions)

    async def match_resume(self, prompt: str) -> MatchResult:
        """Match resume with JD and return score with suggestions"""
        data = await self.provider.send_prompt(prompt)
        raw_content = self.provider._extract_content(data)

        # Parse response into structured format
        match_score, breakdown = self._parse_match_score(raw_content)
        suggestions = self._parse_suggestions(raw_content, include_action=True)

        return MatchResult(
            match_score=match_score,
            match_breakdown=breakdown,
            suggestions=suggestions,
        )

    async def optimize_resume(self, prompt: str) -> OptimizeResult:
        """Optimize resume and return improved content"""
        data = await self.provider.send_prompt(prompt)
        raw_content = self.provider._extract_content(data)
        return OptimizeResult(optimized_content=raw_content)

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
            except json.JSONDecodeError:
                pass

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
            except json.JSONDecodeError:
                pass
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

    def _parse_match_score(self, content: str) -> tuple[int, MatchBreakdown]:
        """Parse match score and breakdown from LLM response"""
        json_data = self._extract_json(content)
        breakdown = MatchBreakdown()
        score = 0

        if json_data and isinstance(json_data, dict):
            score = int(json_data.get("match_score", 0))
            bd = json_data.get("match_breakdown", {})
            breakdown = MatchBreakdown(
                skills_match=int(bd.get("skills_match", 0)),
                experience_match=int(bd.get("experience_match", 0)),
                education_match=int(bd.get("education_match", 0)),
                keywords_match=int(bd.get("keywords_match", 0)),
            )
        return score, breakdown


# Singleton instance
_llm_service_instance: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create LLM service instance"""
    global _llm_service_instance
    if _llm_service_instance is None:
        _llm_service_instance = LLMService()
    return _llm_service_instance
