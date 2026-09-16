"""
Tests for the resume RAG knowledge base and analyze job integration.
"""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.jobs.job_manager import Job, JobManager
from app.services.prompt.builder import PromptBuilder
from app.services.rag.embedder import GeminiEmbedder
from app.services.rag.knowledge_base import (
    KNOWLEDGE_DOCUMENTS,
    STORE_FILENAME,
    build_knowledge_base,
    compute_documents_hash,
    get_store,
    reset_knowledge_base,
)
from app.services.rag.retriever import MAX_QUERY_CHARS, _sync_retrieve, retrieve


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

    def test_build_knowledge_base_populates_persisted_store(self, tmp_path):
        store = build_knowledge_base(
            embedder=FakeEmbedder(),
            persist_dir=tmp_path / ".rag_store",
        )

        assert store.count() == len(KNOWLEDGE_DOCUMENTS)
        assert (tmp_path / ".rag_store" / STORE_FILENAME).exists()

    def test_build_knowledge_base_is_idempotent(self, tmp_path):
        persist_dir = tmp_path / ".rag_store"
        embedder = FakeEmbedder()
        embedder.batch_calls = 0
        original_batch = embedder.embed_batch

        def counting_batch(texts):
            embedder.batch_calls += 1
            return original_batch(texts)

        embedder.embed_batch = counting_batch

        first = build_knowledge_base(
            embedder=embedder,
            persist_dir=persist_dir,
        )
        reset_knowledge_base()
        second = build_knowledge_base(
            embedder=embedder,
            persist_dir=persist_dir,
        )

        assert first.count() == len(KNOWLEDGE_DOCUMENTS)
        assert second.count() == len(KNOWLEDGE_DOCUMENTS)
        assert embedder.batch_calls == 1

    def test_build_stores_documents_hash(self, tmp_path):
        store = build_knowledge_base(
            embedder=FakeEmbedder(),
            persist_dir=tmp_path / ".rag_store",
        )
        assert store.documents_hash == compute_documents_hash()

    def test_rebuild_when_documents_hash_stale(self, tmp_path):
        persist_dir = tmp_path / ".rag_store"
        build_knowledge_base(embedder=FakeEmbedder(), persist_dir=persist_dir)
        reset_knowledge_base()

        path = persist_dir / STORE_FILENAME
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["documents_hash"] = "stale"
        path.write_text(json.dumps(payload), encoding="utf-8")

        class CountingEmbedder(FakeEmbedder):
            batch_calls = 0

            def embed_batch(self, texts):
                CountingEmbedder.batch_calls += 1
                return super().embed_batch(texts)

        reset_knowledge_base()
        build_knowledge_base(embedder=CountingEmbedder(), persist_dir=persist_dir)
        assert CountingEmbedder.batch_calls == 1

    def test_get_store_rejects_partial_or_stale_store(self, tmp_path):
        persist_dir = tmp_path / ".rag_store"
        build_knowledge_base(embedder=FakeEmbedder(), persist_dir=persist_dir)
        reset_knowledge_base()

        path = persist_dir / STORE_FILENAME
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["documents_hash"] = "stale"
        path.write_text(json.dumps(payload), encoding="utf-8")

        assert get_store(persist_dir=persist_dir) is None


class TestRetriever:
    def setup_method(self):
        reset_knowledge_base()

    def test_sync_retrieve_respects_top_k(self, tmp_path):
        store = build_knowledge_base(
            embedder=FakeEmbedder(),
            persist_dir=tmp_path / ".rag_store",
        )

        with patch("app.services.rag.retriever.get_store", return_value=store):
            results = _sync_retrieve(
                "Python resume with measurable API latency improvements",
                top_k=3,
                embedder=FakeEmbedder(),
            )

        assert len(results) == 3
        assert all(isinstance(result, str) for result in results)

    def test_sync_retrieve_truncates_long_query(self, tmp_path):
        store = build_knowledge_base(
            embedder=FakeEmbedder(),
            persist_dir=tmp_path / ".rag_store",
        )

        embedded_queries: list[str] = []

        class RecordingEmbedder(FakeEmbedder):
            def embed(self, text: str) -> list[float]:
                embedded_queries.append(text)
                return super().embed(text)

        long_query = "x" * (MAX_QUERY_CHARS + 500)
        with patch("app.services.rag.retriever.get_store", return_value=store):
            _sync_retrieve(long_query, top_k=3, embedder=RecordingEmbedder())

        assert len(embedded_queries) == 1
        assert len(embedded_queries[0]) == MAX_QUERY_CHARS

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
async def test_execute_analyze_job_passes_retrieved_context_to_prompt_builder():
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

    builder = PromptBuilder()
    job = Job(
        job_id="job-1",
        job_type="analyze",
        payload=SimpleNamespace(session_id="session-123"),
    )
    job_manager = JobManager(max_queue_size=1)

    with (
        patch(
            "app.services.rag.retrieve",
            new=AsyncMock(return_value=["RAG context"]),
        ),
        patch(
            "app.services.validators.content_moderator.get_content_moderator",
        ) as moderator_factory,
        patch.object(
            builder,
            "build_analyze_prompt",
            wraps=builder.build_analyze_prompt,
        ) as build_prompt,
    ):
        moderator_factory.return_value.check_input.return_value = (True, None)

        result = await job_manager._execute_job(
            job,
            lambda: llm,
            lambda: builder,
            AsyncMock(return_value="Resume text"),
        )

    assert result["suggestions"][0]["title"] == "Add metrics"
    build_prompt.assert_called_once_with(
        "Resume text",
        retrieved_context=["RAG context"],
    )
    llm.analyze_resume.assert_awaited_once()
