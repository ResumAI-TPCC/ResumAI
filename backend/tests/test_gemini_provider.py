"""
Tests for Gemini LLM Provider (using new google-genai SDK)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.llm.base import LLMResponse, MatchScoreResult


@pytest.fixture
def mock_env_config():
    """Mock env_config with nested structure"""
    with patch("app.services.llm.gemini.env_config") as mock:
        # Create nested mock structure
        mock.llm.gemini.api_key = "test_api_key"
        mock.llm.gemini.model = "gemini-2.5-flash"
        yield mock


@pytest.fixture
def mock_genai():
    with patch("app.services.llm.gemini.genai") as mock:
        yield mock


class TestGeminiProvider:
    def test_provider_name(self, mock_env_config, mock_genai):
        from app.services.llm.gemini import GeminiProvider

        provider = GeminiProvider()
        assert provider.provider_name == "gemini"

    def test_init_without_api_key(self):
        with patch("app.services.llm.gemini.env_config") as mock_env_config:
            mock_env_config.llm.gemini.api_key = ""
            with pytest.raises(ValueError, match="GEMINI_API_KEY is required"):
                from app.services.llm.gemini import GeminiProvider

                GeminiProvider()

    def test_client_initialized_with_api_key(self, mock_env_config, mock_genai):
        from app.services.llm.gemini import GeminiProvider

        provider = GeminiProvider()

        # Verify client was created with API key from env_config
        mock_genai.Client.assert_called_once_with(api_key="test_api_key")
        assert provider.model_name == "gemini-2.5-flash"

    @pytest.mark.asyncio
    async def test_optimize(self, mock_env_config, mock_genai):
        from app.services.llm.gemini import GeminiProvider

        # Setup mock response
        mock_response = MagicMock()
        mock_response.text = "Optimized resume content"
        mock_response.usage_metadata = MagicMock(
            prompt_token_count=100,
            candidates_token_count=200,
            total_token_count=300,
        )

        # Setup async mock for client.aio.models.generate_content
        mock_aio_models = MagicMock()
        mock_aio_models.generate_content = AsyncMock(return_value=mock_response)
        mock_aio = MagicMock()
        mock_aio.models = mock_aio_models
        mock_client = MagicMock()
        mock_client.aio = mock_aio
        mock_genai.Client.return_value = mock_client

        provider = GeminiProvider()
        result = await provider.optimize(
            resume_content="Original resume",
            job_description="Software Engineer position",
            instructions="Focus on Python skills",
        )

        assert isinstance(result, LLMResponse)
        assert result.content == "Optimized resume content"
        assert result.model == "gemini-2.5-flash"
        assert result.usage["total_tokens"] == 300

    @pytest.mark.asyncio
    async def test_analyze(self, mock_env_config, mock_genai):
        from app.services.llm.gemini import GeminiProvider

        # Setup mock response
        mock_response = MagicMock()
        mock_response.text = "Analysis results"
        mock_response.usage_metadata = MagicMock(
            prompt_token_count=100,
            candidates_token_count=200,
            total_token_count=300,
        )

        # Setup async mock
        mock_aio_models = MagicMock()
        mock_aio_models.generate_content = AsyncMock(return_value=mock_response)
        mock_aio = MagicMock()
        mock_aio.models = mock_aio_models
        mock_client = MagicMock()
        mock_client.aio = mock_aio
        mock_genai.Client.return_value = mock_client

        provider = GeminiProvider()
        result = await provider.analyze(
            resume_content="Resume content",
            job_description="Job description",
        )

        assert isinstance(result, LLMResponse)
        assert result.content == "Analysis results"
        assert result.model == "gemini-2.5-flash"

    @pytest.mark.asyncio
    async def test_match(self, mock_env_config, mock_genai):
        from app.services.llm.gemini import GeminiProvider

        # Setup mock response with valid JSON
        mock_response = MagicMock()
        mock_response.text = '{"score": 0.85, "explanation": "Good match", "suggestions": ["Add more keywords"]}'
        mock_response.usage_metadata = None

        # Setup async mock
        mock_aio_models = MagicMock()
        mock_aio_models.generate_content = AsyncMock(return_value=mock_response)
        mock_aio = MagicMock()
        mock_aio.models = mock_aio_models
        mock_client = MagicMock()
        mock_client.aio = mock_aio
        mock_genai.Client.return_value = mock_client

        provider = GeminiProvider()
        result = await provider.match(
            resume_content="Resume content",
            job_description="Job description",
        )

        assert isinstance(result, MatchScoreResult)
        assert result.score == 0.85
        assert result.explanation == "Good match"
        assert "Add more keywords" in result.suggestions

    @pytest.mark.asyncio
    async def test_match_with_markdown_json(self, mock_env_config, mock_genai):
        from app.services.llm.gemini import GeminiProvider

        # Setup mock response with JSON wrapped in markdown code block
        mock_response = MagicMock()
        mock_response.text = '```json\n{"score": 0.75, "explanation": "Decent match", "suggestions": ["Improve formatting"]}\n```'
        mock_response.usage_metadata = None

        # Setup async mock
        mock_aio_models = MagicMock()
        mock_aio_models.generate_content = AsyncMock(return_value=mock_response)
        mock_aio = MagicMock()
        mock_aio.models = mock_aio_models
        mock_client = MagicMock()
        mock_client.aio = mock_aio
        mock_genai.Client.return_value = mock_client

        provider = GeminiProvider()
        result = await provider.match(
            resume_content="Resume content",
            job_description="Job description",
        )

        assert isinstance(result, MatchScoreResult)
        assert result.score == 0.75

    @pytest.mark.asyncio
    async def test_match_invalid_json(self, mock_env_config, mock_genai):
        from app.services.llm.gemini import GeminiProvider

        # Setup mock response with invalid JSON
        mock_response = MagicMock()
        mock_response.text = "This is not valid JSON"
        mock_response.usage_metadata = None

        # Setup async mock
        mock_aio_models = MagicMock()
        mock_aio_models.generate_content = AsyncMock(return_value=mock_response)
        mock_aio = MagicMock()
        mock_aio.models = mock_aio_models
        mock_client = MagicMock()
        mock_client.aio = mock_aio
        mock_genai.Client.return_value = mock_client

        provider = GeminiProvider()
        result = await provider.match(
            resume_content="Resume content",
            job_description="Job description",
        )

        # Should return default result on parse failure
        assert isinstance(result, MatchScoreResult)
        assert result.score == 0.5
        assert "Error parsing response" in result.explanation
