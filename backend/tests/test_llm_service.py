"""
Unit Tests for RA-38: LLM Service - Send Prompt to LLM and Handle Response

Tests the LLM service layer including:
- Base provider interface
- Provider factory
- Mock provider implementation for testing
- Response handling
"""

import pytest
from typing import Optional
from unittest.mock import patch

from app.services.llm import (
    BaseLLMProvider,
    LLMResponse,
    MatchScoreResult,
    get_llm_provider,
    register_provider,
)
from app.services.llm.factory import clear_provider_cache, _provider_registry


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


class TestProviderFactory:
    """Test suite for LLM Provider factory."""

    def setup_method(self):
        """Reset provider registry and cache before each test."""
        clear_provider_cache()
        _provider_registry.clear()

    def test_register_provider(self):
        """Test registering a provider."""
        register_provider("mock", MockLLMProvider)

        assert "mock" in _provider_registry
        assert _provider_registry["mock"] == MockLLMProvider

    def test_get_provider_returns_instance(self):
        """Test getting registered provider."""
        register_provider("mock", MockLLMProvider)

        with patch("app.services.llm.factory.settings") as mock_settings:
            mock_settings.LLM_PROVIDER = "mock"
            provider = get_llm_provider()

            assert isinstance(provider, MockLLMProvider)

    def test_get_provider_singleton(self):
        """Test that get_llm_provider returns singleton."""
        register_provider("mock", MockLLMProvider)

        with patch("app.services.llm.factory.settings") as mock_settings:
            mock_settings.LLM_PROVIDER = "mock"
            provider1 = get_llm_provider()
            provider2 = get_llm_provider()

            assert provider1 is provider2

    def test_get_provider_no_registry_raises(self):
        """Test that get_llm_provider raises when no provider registered."""
        with pytest.raises(ValueError, match="No LLM Provider registered"):
            get_llm_provider()

    def test_get_provider_unsupported_raises(self):
        """Test that get_llm_provider raises for unsupported provider."""
        register_provider("mock", MockLLMProvider)

        with patch("app.services.llm.factory.settings") as mock_settings:
            mock_settings.LLM_PROVIDER = "unsupported"
            with pytest.raises(ValueError, match="Unsupported LLM Provider"):
                get_llm_provider()

    def test_clear_provider_cache(self):
        """Test clearing provider cache."""
        register_provider("mock", MockLLMProvider)

        with patch("app.services.llm.factory.settings") as mock_settings:
            mock_settings.LLM_PROVIDER = "mock"
            provider1 = get_llm_provider()
            clear_provider_cache()
            provider2 = get_llm_provider()

            # After clearing, should get new instance
            assert provider1 is not provider2


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

        # Verify response is valid JSON with expected structure
        data = json.loads(response.content)
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)

    @pytest.mark.asyncio
    async def test_analyze_suggestion_structure(self, provider):
        """Test analyze returns suggestions with correct structure."""
        import json

        response = await provider.analyze(
            resume_content="Test Resume",
            job_description="Test JD",
        )

        data = json.loads(response.content)
        suggestion = data["suggestions"][0]

        # Verify suggestion has all required fields
        assert "category" in suggestion
        assert "priority" in suggestion
        assert "title" in suggestion
        assert "description" in suggestion
        assert "example" in suggestion

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


class TestLLMResponseParsing:
    """Test suite for LLM response parsing utilities."""

    def test_parse_json_suggestions(self):
        """Test parsing JSON suggestions from LLM response."""
        import json

        response_content = '''
        {
            "suggestions": [
                {
                    "category": "content",
                    "priority": "high",
                    "title": "Add quantifiable metrics",
                    "description": "Your achievements lack specific numbers",
                    "example": "Increased sales by 25%"
                },
                {
                    "category": "skills",
                    "priority": "medium",
                    "title": "Add relevant keywords",
                    "description": "Include industry-specific terms",
                    "example": "Add 'Agile', 'Scrum' methodologies"
                }
            ]
        }
        '''

        data = json.loads(response_content)

        assert len(data["suggestions"]) == 2
        assert data["suggestions"][0]["category"] == "content"
        assert data["suggestions"][1]["priority"] == "medium"

    def test_parse_malformed_json_raises(self):
        """Test that malformed JSON raises exception."""
        import json

        malformed_json = '{"suggestions": [{"broken": }]}'

        with pytest.raises(json.JSONDecodeError):
            json.loads(malformed_json)

    def test_extract_json_from_markdown(self):
        """Test extracting JSON from markdown code block."""
        import json
        import re

        response_with_markdown = '''
        Here is my analysis:

        ```json
        {
            "suggestions": [
                {"category": "format", "priority": "low", "title": "Fix formatting"}
            ]
        }
        ```
        '''

        # Extract JSON from markdown code block
        pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        match = re.search(pattern, response_with_markdown)

        if match:
            json_str = match.group(1)
            data = json.loads(json_str)
            assert "suggestions" in data


class TestErrorHandling:
    """Test suite for error handling in LLM service."""

    @pytest.mark.asyncio
    async def test_handle_empty_resume_content(self):
        """Test handling of empty resume content."""
        provider = MockLLMProvider()

        # Should still work with empty content (validation is in prompt builder)
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
