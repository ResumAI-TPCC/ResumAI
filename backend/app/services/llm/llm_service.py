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
        
        # Parse response into structured format
        suggestions = self._parse_suggestions(response.content, include_example=True)
        return AnalyzeResult(suggestions=suggestions)

    async def match_resume(self, prompt: str) -> MatchResult:
        """Match resume with JD and return score with suggestions"""
        response = await self.provider.match(prompt, "")  # Pass empty string for job_description
        
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
        return OptimizeResult(optimized_content=response.content)

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


@lru_cache
def get_llm_service() -> LLMService:
    """Get cached LLM service instance (singleton pattern)"""
    return LLMService()
