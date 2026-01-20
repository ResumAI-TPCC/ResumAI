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
from .exceptions import LLMResponseError

logger = logging.getLogger(__name__)


class LLMService:
    """
    LLM Service class - Middle layer

    Responsibilities:
    - Receive prompts from API endpoints
    - Send prompts to LLM Provider (Gemini)
    - Parse LLM responses into structured formats
    - Return data matching API response schemas
    """

    def __init__(self):
        """Initialize LLM service with Gemini provider"""
        self.provider = GeminiProvider()

    async def analyze_resume(self, prompt: str) -> AnalyzeResult:
        """
        Analyze resume and return structured suggestions

        Args:
            prompt: Complete prompt for resume analysis (constructed by upstream)

        Returns:
            AnalyzeResult: Structured analysis with suggestions list
        """
        # Send prompt to LLM
        data = await self.provider.send_prompt(prompt)
        raw_content = self.provider._extract_content(data)

        # Parse response into structured format
        suggestions = self._parse_suggestions(raw_content, include_example=True)

        return AnalyzeResult(suggestions=suggestions)

    async def match_resume(self, prompt: str) -> MatchResult:
        """
        Match resume with job description and return score with suggestions

        Args:
            prompt: Complete prompt for matching (constructed by upstream)

        Returns:
            MatchResult: Match score, breakdown, and suggestions
        """
        # Send prompt to LLM
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
        """
        Optimize resume and return improved content

        Args:
            prompt: Complete prompt for optimization (constructed by upstream)

        Returns:
            OptimizeResult: Optimized resume content
        """
        # Send prompt to LLM
        data = await self.provider.send_prompt(prompt)
        raw_content = self.provider._extract_content(data)

        return OptimizeResult(optimized_content=raw_content)

    async def send_raw_prompt(self, prompt: str) -> str:
        """
        Send prompt and return raw response content

        Args:
            prompt: Any prompt to send to LLM

        Returns:
            str: Raw response content from LLM
        """
        data = await self.provider.send_prompt(prompt)
        return self.provider._extract_content(data)

    def _parse_suggestions(
        self,
        content: str,
        include_example: bool = False,
        include_action: bool = False,
    ) -> list[Suggestion]:
        """
        Parse LLM response content to extract suggestions

        Attempts to parse JSON format first, falls back to text parsing
        """
        suggestions = []

        # Try to extract JSON from response
        json_data = self._extract_json(content)
        if json_data:
            suggestions = self._parse_suggestions_from_json(
                json_data, include_example, include_action
            )
            if suggestions:
                return suggestions

        # Fallback: parse as structured text
        suggestions = self._parse_suggestions_from_text(
            content, include_example, include_action
        )

        return suggestions

    def _extract_json(self, content: str) -> Optional[dict]:
        """Extract JSON object or array from content"""
        # Try to find JSON in code blocks
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to parse entire content as JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try to find JSON object or array
        json_patterns = [
            r"\{[\s\S]*\}",  # Object
            r"\[[\s\S]*\]",  # Array
        ]
        for pattern in json_patterns:
            match = re.search(pattern, content)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    continue

        return None

    def _parse_suggestions_from_json(
        self,
        data: dict,
        include_example: bool,
        include_action: bool,
    ) -> list[Suggestion]:
        """Parse suggestions from JSON data"""
        suggestions = []

        # Handle different JSON structures
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("suggestions", [])
            if not items:
                # Maybe the entire dict is a single suggestion
                if "title" in data or "category" in data:
                    items = [data]

        for item in items:
            if not isinstance(item, dict):
                continue

            suggestion = Suggestion(
                category=str(item.get("category", "general")),
                priority=str(item.get("priority", "medium")),
                title=str(item.get("title", "")),
                description=str(item.get("description", "")),
            )

            if include_example:
                suggestion.example = item.get("example")
            if include_action:
                suggestion.action = item.get("action")

            if suggestion.title or suggestion.description:
                suggestions.append(suggestion)

        return suggestions

    def _parse_suggestions_from_text(
        self,
        content: str,
        include_example: bool,
        include_action: bool,
    ) -> list[Suggestion]:
        """
        Fallback parser for text-based responses

        Looks for numbered lists or bullet points
        """
        suggestions = []
        lines = content.split("\n")

        current_suggestion = None
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for numbered item or bullet point (new suggestion)
            if re.match(r"^(\d+[\.\)]\s*|[-*•]\s*)", line):
                if current_suggestion and (
                    current_suggestion.get("title")
                    or current_suggestion.get("description")
                ):
                    suggestions.append(
                        self._create_suggestion_from_dict(
                            current_suggestion, include_example, include_action
                        )
                    )

                # Start new suggestion
                text = re.sub(r"^(\d+[\.\)]\s*|[-*•]\s*)", "", line).strip()
                current_suggestion = {
                    "title": text,
                    "description": "",
                    "category": "general",
                    "priority": self._infer_priority(text),
                }

            elif current_suggestion:
                # Add to current suggestion description
                current_suggestion["description"] += " " + line

        # Don't forget the last suggestion
        if current_suggestion and (
            current_suggestion.get("title") or current_suggestion.get("description")
        ):
            suggestions.append(
                self._create_suggestion_from_dict(
                    current_suggestion, include_example, include_action
                )
            )

        return suggestions

    def _create_suggestion_from_dict(
        self,
        data: dict,
        include_example: bool,
        include_action: bool,
    ) -> Suggestion:
        """Create Suggestion object from dictionary"""
        suggestion = Suggestion(
            category=data.get("category", "general"),
            priority=data.get("priority", "medium"),
            title=data.get("title", "").strip(),
            description=data.get("description", "").strip(),
        )
        if include_example:
            suggestion.example = data.get("example")
        if include_action:
            suggestion.action = data.get("action")
        return suggestion

    def _infer_priority(self, text: str) -> str:
        """Infer priority from text content"""
        text_lower = text.lower()
        if any(word in text_lower for word in ["critical", "must", "essential"]):
            return "high"
        elif any(word in text_lower for word in ["should", "recommend", "important"]):
            return "medium"
        return "low"

    def _parse_match_score(self, content: str) -> tuple[int, MatchBreakdown]:
        """
        Parse match score and breakdown from LLM response

        Returns:
            tuple: (overall_score, MatchBreakdown)
        """
        breakdown = MatchBreakdown()
        overall_score = 0

        # Try to extract JSON first
        json_data = self._extract_json(content)
        if json_data and isinstance(json_data, dict):
            overall_score = int(json_data.get("match_score", 0))
            if "match_breakdown" in json_data:
                bd = json_data["match_breakdown"]
                breakdown = MatchBreakdown(
                    skills_match=int(bd.get("skills_match", 0)),
                    experience_match=int(bd.get("experience_match", 0)),
                    education_match=int(bd.get("education_match", 0)),
                    keywords_match=int(bd.get("keywords_match", 0)),
                )
            return overall_score, breakdown

        # Fallback: extract numbers from text
        score_patterns = [
            r"(?:overall|total|match)\s*(?:score)?[:\s]*(\d+)",
            r"(\d+)\s*(?:out of\s*100|%|/100)",
        ]
        for pattern in score_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                overall_score = min(100, max(0, int(match.group(1))))
                break

        # Try to extract breakdown scores
        breakdown_patterns = {
            "skills_match": r"skills?\s*(?:match)?[:\s]*(\d+)",
            "experience_match": r"experience\s*(?:match)?[:\s]*(\d+)",
            "education_match": r"education\s*(?:match)?[:\s]*(\d+)",
            "keywords_match": r"keywords?\s*(?:match)?[:\s]*(\d+)",
        }
        for field, pattern in breakdown_patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                setattr(breakdown, field, min(100, max(0, int(match.group(1)))))

        return overall_score, breakdown


# Singleton instance for convenience
_llm_service_instance: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create LLM service instance"""
    global _llm_service_instance
    if _llm_service_instance is None:
        _llm_service_instance = LLMService()
    return _llm_service_instance
