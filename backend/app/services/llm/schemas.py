"""
Response schemas for LLM Service
Defines the structured data formats for API responses
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Suggestion:
    """Single suggestion item"""
    category: str
    priority: str  # "high", "medium", "low"
    title: str
    description: str
    example: Optional[str] = None  # Used in analyze response
    action: Optional[str] = None   # Used in match response


@dataclass
class AnalyzeResult:
    """Result for analyze endpoint"""
    suggestions: List[Suggestion] = field(default_factory=list)


@dataclass
class MatchBreakdown:
    """Match score breakdown by category"""
    skills_match: int = 0
    experience_match: int = 0
    education_match: int = 0
    keywords_match: int = 0


@dataclass
class MatchResult:
    """Result for match endpoint"""
    match_score: int = 0
    match_breakdown: MatchBreakdown = field(default_factory=MatchBreakdown)
    suggestions: List[Suggestion] = field(default_factory=list)


@dataclass
class OptimizeResult:
    """Result for optimize endpoint"""
    optimized_content: str = ""  # The optimized resume text
