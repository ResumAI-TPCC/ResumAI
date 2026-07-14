"""
Tests for the resume RAG knowledge base and analyze integration.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.routes import resumes as resume_routes
from app.schemas.resume_schema import ResumeAnalyzeRequest
from app.services.prompt.builder import PromptBuilder
from app.services.rag.embedder import GeminiEmbedder
from app.services.rag.knowledge_base import (
    COLLECTION_NAME,
    KNOWLEDGE_DOCUMENTS,
    build_knowledge_base,
    reset_knowledge_base,
)
from app.services.rag.retriever import _sync_retrieve, retrieve


def fake_embedding(text: str, dim: int = 8) -> list[float]:
    seed = sum(ord(char) for char in text)
    values = [float((seed + index) % 11 + 1) for index in range(dim)]
    norm = sum(value * value for value in values) ** 0.5
    return [value / norm for value in values]


class FakeEmbedder:
    def embed(self, text: str) -> list[float]:
        return fake_embedding(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]


class TestGeminiEmbedder:
    def test_missing_api_key_fails_fast(self):
        with patch("app.services.rag.embedder.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = ""
            mock_settings.GEMINI_EMBEDDING_MODEL = "fake-model"

            with pytest.raises(ValueError, match="GEMINI_API_KEY"):
                GeminiEmbedder(api_key="")

    def test_embed_delegates_to_embeddings_client(self):
        client = MagicMock()
        client.embed_query.return_value = [0.1, 0.2, 0.3]

        embedder = GeminiEmbedder.__new__(GeminiEmbedder)
        embedder.client = client
        embedder.model = "test-embedding-model"

        assert embedder.embed("resume text") == [0.1, 0.2, 0.3]
        client.embed_query.assert_called_once_with("resume text")

    def test_embed_rejects_empty_text(self):
        embedder = GeminiEmbedder.__new__(GeminiEmbedder)
        embedder.client = MagicMock()
        embedder.model = "test-embedding-model"

        with pytest.raises(ValueError, match="empty"):
            embedder.embed(" ")


class TestKnowledgeBase:
    def setup_method(self):
        reset_knowledge_base()

    def test_curated_documents_cover_expected_seed_set(self):
        assert len(KNOWLEDGE_DOCUMENTS) == 10
        assert {doc["category"] for doc in KNOWLEDGE_DOCUMENTS} >= {
            "ats",
            "content",
            "format",
            "skills",
            "structure",
        }

    def test_document_ids_are_unique_and_complete(self):
        ids = [doc["id"] for doc in KNOWLEDGE_DOCUMENTS]

        assert len(ids) == len(set(ids))
        for doc in KNOWLEDGE_DOCUMENTS:
            assert doc["id"]
            assert doc["category"]
            assert doc["title"]
            assert doc["content"].strip()

    def test_build_knowledge_base_populates_persisted_collection(self, tmp_path):
        collection = build_knowledge_base(
            embedder=FakeEmbedder(),
            persist_dir=tmp_path / ".chroma_db",
        )

        assert collection.name == COLLECTION_NAME
        assert collection.count() == len(KNOWLEDGE_DOCUMENTS)

    def test_build_knowledge_base_is_idempotent(self, tmp_path):
        persist_dir = tmp_path / ".chroma_db"

        first = build_knowledge_base(
            embedder=FakeEmbedder(),
            persist_dir=persist_dir,
        )
        reset_knowledge_base()
        second = build_knowledge_base(
            embedder=FakeEmbedder(),
            persist_dir=persist_dir,
        )

        assert first.count() == len(KNOWLEDGE_DOCUMENTS)
        assert second.count() == len(KNOWLEDGE_DOCUMENTS)


class TestRetriever:
    def setup_method(self):
        reset_knowledge_base()

    def test_sync_retrieve_respects_top_k(self, tmp_path):
        collection = build_knowledge_base(
            embedder=FakeEmbedder(),
            persist_dir=tmp_path / ".chroma_db",
        )

        with patch("app.services.rag.retriever.get_collection", return_value=collection):
            results = _sync_retrieve(
                "Python resume with measurable API latency improvements",
                top_k=3,
                embedder=FakeEmbedder(),
            )

        assert len(results) == 3
        assert all(isinstance(result, str) for result in results)

    @pytest.mark.asyncio
    async def test_retrieve_returns_empty_for_blank_query(self):
        assert await retrieve(" ") == []

    @pytest.mark.asyncio
    async def test_retrieve_degrades_to_empty_list_on_failure(self):
        with patch("app.services.rag.retriever._sync_retrieve", side_effect=RuntimeError):
            assert await retrieve("resume text") == []


class TestPromptBuilderRagIntegration:
    def test_analyze_prompt_without_rag_context(self):
        messages = PromptBuilder().build_analyze_prompt("Jane Doe\nEngineer")
        prompt = "\n".join(message.content for message in messages)

        assert "Jane Doe" in prompt
        assert "Industry Best Practices" not in prompt

    def test_analyze_prompt_injects_rag_context(self):
        messages = PromptBuilder().build_analyze_prompt(
            "Jane Doe\nEngineer",
            retrieved_context=[
                "Use strong action verbs.",
                "",
                "Quantify outcomes with credible metrics.",
            ],
        )
        prompt = "\n".join(message.content for message in messages)

        assert "Industry Best Practices" in prompt
        assert "- Use strong action verbs." in prompt
        assert "- Quantify outcomes with credible metrics." in prompt
        assert "- \n" not in prompt


@pytest.mark.asyncio
async def test_analyze_route_passes_retrieved_context_to_prompt_builder():
    llm = MagicMock()
    llm.analyze_resume = AsyncMock(
        return_value=SimpleNamespace(
            suggestions=[
                SimpleNamespace(
                    category="content",
                    priority="high",
                    title="Add metrics",
                    description="Impact is not quantified.",
                    example="Improved latency by 40%.",
                )
            ]
        )
    )

    with (
        patch.object(resume_routes, "get_resume_content", new=AsyncMock(return_value="Resume text")),
        patch.object(resume_routes, "retrieve_rag_context", new=AsyncMock(return_value=["RAG context"])),
        patch.object(resume_routes, "get_llm_service", return_value=llm),
        patch.object(resume_routes, "get_content_moderator") as moderator_factory,
        patch.object(
            resume_routes.get_prompt_builder(),
            "build_analyze_prompt",
            wraps=resume_routes.get_prompt_builder().build_analyze_prompt,
        ) as build_prompt,
    ):
        moderator_factory.return_value.check_input.return_value = (True, None)

        response = await resume_routes.analyze_resume(
            ResumeAnalyzeRequest(session_id="session-123")
        )

    assert response.code == 200
    build_prompt.assert_called_once_with(
        "Resume text",
        retrieved_context=["RAG context"],
    )
