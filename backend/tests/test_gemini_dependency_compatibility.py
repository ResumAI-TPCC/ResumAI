"""Exercise real LangChain chains with only the Gemini transport mocked."""

from unittest.mock import patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_google_genai import ChatGoogleGenerativeAI

from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.schemas import AnalyzeResult, MatchResult


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "operation,schema,payload",
    [
        (
            "analyze",
            AnalyzeResult,
            {"suggestions": [{"category": "content", "priority": "high",
                              "title": "Add metrics", "description": "Quantify impact"}]},
        ),
        (
            "match",
            MatchResult,
            {"match_score": 83, "match_breakdown": {"skills_match": 90},
             "suggestions": []},
        ),
    ],
)
async def test_structured_chains_parse_gemini_tool_calls(operation, schema, payload):
    response = ChatResult(generations=[ChatGeneration(message=AIMessage(
        content="",
        tool_calls=[{"name": schema.__name__, "args": payload, "id": "test-call"}],
    ))])
    with patch.object(ChatGoogleGenerativeAI, "_agenerate", autospec=True) as api:
        api.return_value = response
        provider = GeminiProvider(api_key="test-key-not-a-real-credential")
        result = await getattr(provider, operation)([HumanMessage(content="Resume")])

    assert isinstance(result, schema)
    assert result == schema.model_validate(payload)
    api.assert_awaited_once()
    assert api.call_args.kwargs["tools"]


@pytest.mark.asyncio
async def test_text_chain_preserves_markdown():
    markdown = "# Resume\n\nImproved latency by 40%."
    response = ChatResult(generations=[ChatGeneration(message=AIMessage(content=markdown))])
    with patch.object(ChatGoogleGenerativeAI, "_agenerate", autospec=True) as api:
        api.return_value = response
        provider = GeminiProvider(api_key="test-key-not-a-real-credential")
        result = await provider.optimize([HumanMessage(content="Resume")])

    assert result.content == markdown
    api.assert_awaited_once()