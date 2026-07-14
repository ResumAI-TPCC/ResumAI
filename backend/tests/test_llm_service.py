"""
Unit Tests for LLM Service

Tests the LLM service layer including:
- Base provider interface
- Mock provider implementation for testing
- Response data classes

Note: TestProviderFactory and TestLLMResponseParsing have been removed because
the factory registry pattern is no longer the primary code path (LLMService now
holds LangChain chains directly), and JSON parsing logic has been replaced by
with_structured_output() which delegates parsing to Gemini Function Calling.
"""

import pytest
from typing import Optional

from app.services.llm import (
    BaseLLMProvider,
    LLMResponse,
    MatchScoreResult,
)


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM Provider for testing purposes."""

    def __init__(self):
        self._call_count = 0
        self._last_prompt = None

    @property
    def provider_name(self) -> str:
        return "mock"

    async def optimize(
        self,
        resume_content: str,
        job_description: str,
        instructions: Optional[str] = None,
    ) -> LLMResponse:
        self._call_count += 1
        self._last_prompt = resume_content
        return LLMResponse(
            content=f"Optimized: {resume_content[:50]}...",
            model="mock-model-v1",
            usage={"prompt_tokens": 100, "completion_tokens": 50},
        )

    async def analyze(
        self,
        resume_content: str,
        job_description: str,
    ) -> LLMResponse:
        self._call_count += 1
        self._last_prompt = resume_content
        return LLMResponse(
            content='{"suggestions": [{"category": "content", "priority": "high", "title": "Add metrics", "description": "Add quantifiable achievements", "example": "Increased sales by 20%"}]}',
            model="mock-model-v1",
            usage={"prompt_tokens": 150, "completion_tokens": 100},
        )

    async def match(
        self,
        resume_content: str,
        job_description: str,
    ) -> MatchScoreResult:
        self._call_count += 1
        return MatchScoreResult(
            score=0.75,
            explanation="Good match with some gaps in required skills",
            suggestions=["Add more Python experience", "Highlight leadership skills"],
        )


class TestLLMResponse:
    """Test suite for LLMResponse data class."""

    def test_llm_response_creation(self):
        """Test creating LLMResponse with all fields."""
        response = LLMResponse(
            content="Test response content",
            model="gpt-4",
            usage={"prompt_tokens": 100, "completion_tokens": 50},
        )

        assert response.content == "Test response content"
        assert response.model == "gpt-4"
        assert response.usage["prompt_tokens"] == 100

    def test_llm_response_optional_usage(self):
        """Test LLMResponse with optional usage field."""
        response = LLMResponse(
            content="Test content",
            model="claude-3",
        )

        assert response.content == "Test content"
        assert response.usage is None


class TestMatchScoreResult:
    """Test suite for MatchScoreResult data class."""

    def test_match_score_result_creation(self):
        """Test creating MatchScoreResult."""
        result = MatchScoreResult(
            score=0.85,
            explanation="Strong match",
            suggestions=["Emphasize leadership"],
        )

        assert result.score == 0.85
        assert result.explanation == "Strong match"
        assert len(result.suggestions) == 1

    def test_match_score_range(self):
        """Test match score is within valid range."""
        result = MatchScoreResult(
            score=0.5,
            explanation="Average match",
            suggestions=[],
        )

        assert 0.0 <= result.score <= 1.0


class TestBaseLLMProvider:
    """Test suite for BaseLLMProvider interface."""

    def test_cannot_instantiate_base_class(self):
        """Test that BaseLLMProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseLLMProvider()

    def test_mock_provider_implements_interface(self):
        """Test that MockLLMProvider properly implements the interface."""
        provider = MockLLMProvider()

        assert hasattr(provider, "optimize")
        assert hasattr(provider, "analyze")
        assert hasattr(provider, "match")
        assert hasattr(provider, "provider_name")

    def test_mock_provider_name(self):
        """Test mock provider returns correct name."""
        provider = MockLLMProvider()
        assert provider.provider_name == "mock"


class TestMockProviderFunctionality:
    """Test suite for MockLLMProvider functionality."""

    @pytest.fixture
    def provider(self):
        """Create a MockLLMProvider instance."""
        return MockLLMProvider()

    @pytest.mark.asyncio
    async def test_optimize_returns_response(self, provider):
        """Test optimize method returns valid response."""
        response = await provider.optimize(
            resume_content="John Doe, Software Engineer",
            job_description="Looking for a senior engineer",
        )

        assert isinstance(response, LLMResponse)
        assert "Optimized" in response.content
        assert response.model == "mock-model-v1"

    @pytest.mark.asyncio
    async def test_analyze_returns_json_response(self, provider):
        """Test analyze method returns JSON response."""
        import json

        response = await provider.analyze(
            resume_content="John Doe, Software Engineer",
            job_description="Senior Engineer position",
        )

        assert isinstance(response, LLMResponse)

        data = json.loads(response.content)
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)

    @pytest.mark.asyncio
    async def test_match_returns_score_result(self, provider):
        """Test match method returns MatchScoreResult."""
        result = await provider.match(
            resume_content="Experienced Python developer",
            job_description="Looking for Python developer",
        )

        assert isinstance(result, MatchScoreResult)
        assert 0.0 <= result.score <= 1.0
        assert result.explanation
        assert isinstance(result.suggestions, list)

    @pytest.mark.asyncio
    async def test_provider_tracks_calls(self, provider):
        """Test that provider tracks method calls."""
        assert provider._call_count == 0

        await provider.optimize("resume", "jd")
        assert provider._call_count == 1

        await provider.analyze("resume", "jd")
        assert provider._call_count == 2

        await provider.match("resume", "jd")
        assert provider._call_count == 3


class TestErrorHandling:
    """Test suite for error handling in LLM service."""

    @pytest.mark.asyncio
    async def test_handle_empty_resume_content(self):
        """Test handling of empty resume content."""
        provider = MockLLMProvider()

        response = await provider.analyze(
            resume_content="",
            job_description="Test JD",
        )

        assert response is not None

    @pytest.mark.asyncio
    async def test_usage_tracking(self):
        """Test that usage information is tracked."""
        provider = MockLLMProvider()

        response = await provider.optimize(
            resume_content="Test resume",
            job_description="Test JD",
        )

        assert response.usage is not None
        assert "prompt_tokens" in response.usage
        assert "completion_tokens" in response.usage
