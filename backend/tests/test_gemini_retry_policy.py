"""Retry and timeout policy of GeminiProvider, with only the Gemini transport mocked."""

from unittest.mock import patch

import pytest
from google.api_core import exceptions as google_exceptions
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings
from app.services.llm.exceptions import LLMAuthenticationError, LLMTimeoutError
from app.services.llm.gemini_provider import GeminiProvider

TEST_KEY = "test-key-not-a-real-credential"


@pytest.fixture(autouse=True)
def no_backoff_sleep():
    """Skip real backoff waits between retries."""
    async def _no_sleep(_seconds):
        return None

    with patch("asyncio.sleep", _no_sleep):
        yield


def _text_response(text: str) -> ChatResult:
    return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])


def test_chat_model_uses_configured_timeout_and_no_inner_retry():
    provider = GeminiProvider(api_key=TEST_KEY)
    model = provider._text_llm.bound

    assert model.timeout == settings.GEMINI_TIMEOUT
    assert model.max_retries == 1


@pytest.mark.asyncio
async def test_auth_error_is_not_retried():
    with patch.object(ChatGoogleGenerativeAI, "_agenerate", autospec=True) as api:
        api.side_effect = google_exceptions.PermissionDenied("API key not valid")
        provider = GeminiProvider(api_key=TEST_KEY)

        with pytest.raises(LLMAuthenticationError):
            await provider.optimize([HumanMessage(content="Resume")])

    assert api.await_count == 1


@pytest.mark.asyncio
async def test_transient_error_is_retried_then_succeeds():
    with patch.object(ChatGoogleGenerativeAI, "_agenerate", autospec=True) as api:
        api.side_effect = [
            google_exceptions.ServiceUnavailable("overloaded"),
            _text_response("# Resume"),
        ]
        provider = GeminiProvider(api_key=TEST_KEY)
        result = await provider.optimize([HumanMessage(content="Resume")])

    assert result.content == "# Resume"
    assert api.await_count == 2


@pytest.mark.asyncio
async def test_timeout_is_retried_then_reported_as_timeout():
    with patch.object(ChatGoogleGenerativeAI, "_agenerate", autospec=True) as api:
        api.side_effect = google_exceptions.DeadlineExceeded("deadline exceeded")
        provider = GeminiProvider(api_key=TEST_KEY)

        with pytest.raises(LLMTimeoutError):
            await provider.optimize([HumanMessage(content="Resume")])

    assert api.await_count == settings.GEMINI_MAX_RETRIES
