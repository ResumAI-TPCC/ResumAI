"""
Unit Tests for RAG Module

Tests cover:
- GeminiEmbedder (mocked API calls)
- Knowledge base build (with injected mock embedder)
- Retriever (end-to-end with in-memory ChromaDB)
- PromptBuilder integration (retrieved_context injection)
"""

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

import chromadb
import pytest

from app.services.rag.embedder import GeminiEmbedder
from app.services.rag.knowledge_base import (
    KNOWLEDGE_DOCUMENTS,
    build_knowledge_base,
    reset_knowledge_base,
)
from app.services.rag.retriever import retrieve, _sync_retrieve
from app.services.prompt.builder import PromptBuilder


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


def make_fake_embedding(text: str, dim: int = 8) -> list[float]:
    """
    Deterministic fake embedding: hash the text to a reproducible unit vector.
    Used so retrieval tests can verify the right document is ranked first
    without calling the real Gemini API.
    """
    seed = hash(text) % (2**31)
    import random
    rng = random.Random(seed)
    raw = [rng.gauss(0, 1) for _ in range(dim)]
    norm = sum(v ** 2 for v in raw) ** 0.5 or 1.0
    return [v / norm for v in raw]


class FakeEmbedder:
    """Mock GeminiEmbedder that returns deterministic vectors (no API calls)."""

    def embed(self, text: str) -> list[float]:
        return make_fake_embedding(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


def build_in_memory_kb(fake_embedder: FakeEmbedder) -> chromadb.Collection:
    """Build an in-memory ChromaDB collection loaded with knowledge documents."""
    client = chromadb.EphemeralClient()
    collection = client.get_or_create_collection(
        name="test_resume_knowledge",
        metadata={"hnsw:space": "cosine"},
    )
    ids = [doc["id"] for doc in KNOWLEDGE_DOCUMENTS]
    texts = [doc["content"] for doc in KNOWLEDGE_DOCUMENTS]
    metadatas = [
        {"category": doc["category"], "title": doc["title"]}
        for doc in KNOWLEDGE_DOCUMENTS
    ]
    embeddings = fake_embedder.embed_batch(texts)
    collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    return collection


# ---------------------------------------------------------------------------
# GeminiEmbedder tests
# ---------------------------------------------------------------------------


class TestGeminiEmbedder:
    def test_raises_without_api_key(self):
        with patch("app.services.rag.embedder.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = ""
            with pytest.raises(ValueError, match="GEMINI_API_KEY"):
                GeminiEmbedder(api_key="")

    def test_embed_returns_floats(self):
        fake_result = MagicMock()
        fake_result.embeddings = [MagicMock(values=[0.1, 0.2, 0.3])]

        mock_client = MagicMock()
        mock_client.models.embed_content.return_value = fake_result

        embedder = GeminiEmbedder.__new__(GeminiEmbedder)
        embedder.client = mock_client
        embedder.api_key = "fake-key"

        result = embedder.embed("Hello world")

        assert result == [0.1, 0.2, 0.3]
        mock_client.models.embed_content.assert_called_once()

    def test_embed_raises_on_empty_text(self):
        embedder = GeminiEmbedder.__new__(GeminiEmbedder)
        embedder.client = MagicMock()
        embedder.api_key = "fake-key"

        with pytest.raises(ValueError, match="empty"):
            embedder.embed("")

    def test_embed_batch_calls_embed_for_each_text(self):
        embedder = GeminiEmbedder.__new__(GeminiEmbedder)
        embedder.api_key = "fake-key"

        call_log = []

        def fake_embed(text):
            call_log.append(text)
            return [0.1, 0.2]

        embedder.embed = fake_embed
        result = embedder.embed_batch(["a", "b", "c"])

        assert len(result) == 3
        assert call_log == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# Knowledge base tests
# ---------------------------------------------------------------------------


class TestKnowledgeBase:
    def setup_method(self):
        reset_knowledge_base()

    def test_knowledge_documents_not_empty(self):
        assert len(KNOWLEDGE_DOCUMENTS) >= 5

    def test_every_document_has_required_fields(self):
        for doc in KNOWLEDGE_DOCUMENTS:
            assert "id" in doc, f"Missing 'id' in {doc}"
            assert "category" in doc, f"Missing 'category' in {doc}"
            assert "title" in doc, f"Missing 'title' in {doc}"
            assert "content" in doc, f"Missing 'content' in {doc}"
            assert doc["content"].strip(), f"Empty content in {doc['id']}"

    def test_document_ids_are_unique(self):
        ids = [doc["id"] for doc in KNOWLEDGE_DOCUMENTS]
        assert len(ids) == len(set(ids)), "Duplicate document IDs found"

    def test_build_knowledge_base_populates_collection(self, tmp_path):
        fake_embedder = FakeEmbedder()
        collection = build_knowledge_base(
            embedder=fake_embedder,
            persist_dir=tmp_path / ".chroma_db",
        )

        assert collection.count() == len(KNOWLEDGE_DOCUMENTS)

    def test_build_knowledge_base_is_idempotent(self, tmp_path):
        """Calling build twice with the same persist dir should not duplicate docs."""
        fake_embedder = FakeEmbedder()
        persist = tmp_path / ".chroma_db"

        build_knowledge_base(embedder=fake_embedder, persist_dir=persist)
        reset_knowledge_base()
        build_knowledge_base(embedder=fake_embedder, persist_dir=persist)

        reset_knowledge_base()
        # Load directly from disk to confirm count
        client = chromadb.PersistentClient(path=str(persist))
        col = client.get_collection("resume_knowledge")
        assert col.count() == len(KNOWLEDGE_DOCUMENTS)

    def test_force_rebuild_refreshes_collection(self, tmp_path):
        fake_embedder = FakeEmbedder()
        persist = tmp_path / ".chroma_db"

        col1 = build_knowledge_base(embedder=fake_embedder, persist_dir=persist)
        reset_knowledge_base()
        col2 = build_knowledge_base(
            embedder=fake_embedder, persist_dir=persist, force_rebuild=True
        )

        assert col2.count() == len(KNOWLEDGE_DOCUMENTS)


# ---------------------------------------------------------------------------
# Retriever tests
# ---------------------------------------------------------------------------


class TestRetriever:
    def setup_method(self):
        reset_knowledge_base()

    def test_sync_retrieve_returns_strings(self, tmp_path):
        fake_embedder = FakeEmbedder()
        collection = build_in_memory_kb(fake_embedder)

        # Patch get_collection to return our in-memory collection
        with patch("app.services.rag.retriever.get_collection", return_value=collection):
            results = _sync_retrieve("action verbs software engineer", top_k=3, embedder=fake_embedder)

        assert isinstance(results, list)
        assert len(results) <= 3
        for r in results:
            assert isinstance(r, str)
            assert len(r) > 0

    def test_sync_retrieve_top_k_respected(self, tmp_path):
        fake_embedder = FakeEmbedder()
        collection = build_in_memory_kb(fake_embedder)

        with patch("app.services.rag.retriever.get_collection", return_value=collection):
            results_1 = _sync_retrieve("resume skills", top_k=1, embedder=fake_embedder)
            results_3 = _sync_retrieve("resume skills", top_k=3, embedder=fake_embedder)

        assert len(results_1) == 1
        assert len(results_3) == 3

    @pytest.mark.asyncio
    async def test_retrieve_async_returns_list(self):
        fake_embedder = FakeEmbedder()
        collection = build_in_memory_kb(fake_embedder)

        with patch("app.services.rag.retriever.get_collection", return_value=collection):
            results = await retrieve("Python developer resume", top_k=2, embedder=fake_embedder)

        assert isinstance(results, list)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_retrieve_returns_empty_on_empty_query(self):
        results = await retrieve("", top_k=3)
        assert results == []

    @pytest.mark.asyncio
    async def test_retrieve_never_raises_on_error(self):
        """RAG failures must not propagate — returns empty list gracefully."""
        with patch(
            "app.services.rag.retriever.get_collection",
            side_effect=RuntimeError("simulated failure"),
        ):
            results = await retrieve("any query", top_k=3)

        assert results == []


# ---------------------------------------------------------------------------
# PromptBuilder integration tests
# ---------------------------------------------------------------------------


class TestPromptBuilderRagIntegration:
    def test_analyze_prompt_without_rag_context(self):
        builder = PromptBuilder()
        prompt = builder.build_analyze_prompt("John Doe\nSoftware Engineer")

        assert "John Doe" in prompt
        assert "Industry Best Practices" not in prompt

    def test_analyze_prompt_with_rag_context_injected(self):
        builder = PromptBuilder()
        rag_chunks = [
            "Use action verbs to start each bullet point.",
            "Quantify achievements with concrete metrics.",
        ]
        prompt = builder.build_analyze_prompt(
            "Jane Smith\nData Scientist", retrieved_context=rag_chunks
        )

        assert "Jane Smith" in prompt
        assert "Industry Best Practices" in prompt
        assert "Use action verbs" in prompt
        assert "Quantify achievements" in prompt

    def test_analyze_prompt_with_empty_rag_list(self):
        """Empty retrieved_context list should produce same prompt as None."""
        builder = PromptBuilder()
        prompt_none = builder.build_analyze_prompt("Resume text", retrieved_context=None)
        prompt_empty = builder.build_analyze_prompt("Resume text", retrieved_context=[])

        assert "Industry Best Practices" not in prompt_none
        assert "Industry Best Practices" not in prompt_empty

    def test_analyze_prompt_filters_blank_chunks(self):
        """Blank or whitespace-only chunks should be silently filtered out."""
        builder = PromptBuilder()
        chunks = ["", "   ", "Genuine tip about resume writing."]
        prompt = builder.build_analyze_prompt("Resume text", retrieved_context=chunks)

        assert "Genuine tip" in prompt
        # Should not have stray empty bullets
        assert "- \n" not in prompt


class TestPromptBuilderMatchRagIntegration:
    """Tests for RAG injection into match prompt."""

    def test_match_prompt_without_rag_context(self):
        builder = PromptBuilder()
        prompt = builder.build_match_prompt(
            "John Doe\nSoftware Engineer",
            "We need a Python developer with 3 years experience",
        )

        assert "John Doe" in prompt
        assert "Python developer" in prompt
        assert "Industry Best Practices" not in prompt

    def test_match_prompt_with_rag_context_injected(self):
        builder = PromptBuilder()
        rag_chunks = [
            "Mirror exact keywords from the job description.",
            "Use standard section headings for ATS compatibility.",
        ]
        prompt = builder.build_match_prompt(
            "Jane Smith\nData Scientist",
            "Looking for a data scientist with ML experience",
            retrieved_context=rag_chunks,
        )

        assert "Jane Smith" in prompt
        assert "data scientist" in prompt
        assert "Industry Best Practices" in prompt
        assert "Mirror exact keywords" in prompt
        assert "ATS compatibility" in prompt

    def test_match_prompt_with_empty_rag_list(self):
        builder = PromptBuilder()
        prompt = builder.build_match_prompt(
            "Resume text",
            "Job description text with enough characters to pass validation",
            retrieved_context=[],
        )
        assert "Industry Best Practices" not in prompt

    def test_match_prompt_filters_blank_chunks(self):
        builder = PromptBuilder()
        chunks = ["", "   ", "Genuine matching tip."]
        prompt = builder.build_match_prompt(
            "Resume text",
            "Job description with enough text to pass the validation check",
            retrieved_context=chunks,
        )
        assert "Genuine matching tip" in prompt
        assert "- \n" not in prompt


class TestPromptBuilderOptimizeRagIntegration:
    """Tests for RAG injection into optimize prompts."""

    def test_optimize_no_jd_without_rag(self):
        builder = PromptBuilder()
        prompt = builder.build_optimize_prompt("John Doe\nEngineer")

        assert "John Doe" in prompt
        assert "Industry Best Practices" not in prompt

    def test_optimize_no_jd_with_rag(self):
        builder = PromptBuilder()
        rag_chunks = [
            "Begin every bullet with a strong action verb.",
            "Quantify at least 50% of bullet points.",
        ]
        prompt = builder.build_optimize_prompt(
            "John Doe\nEngineer", retrieved_context=rag_chunks
        )

        assert "John Doe" in prompt
        assert "Industry Best Practices" in prompt
        assert "strong action verb" in prompt

    def test_optimize_with_jd_and_rag(self):
        builder = PromptBuilder()
        rag_chunks = ["Tailor the summary for each role."]
        prompt = builder.build_optimize_prompt(
            "Jane Smith\nDeveloper",
            job_description="Looking for a full-stack developer",
            retrieved_context=rag_chunks,
        )

        assert "Jane Smith" in prompt
        assert "full-stack developer" in prompt
        assert "Industry Best Practices" in prompt
        assert "Tailor the summary" in prompt

    def test_optimize_with_jd_without_rag(self):
        builder = PromptBuilder()
        prompt = builder.build_optimize_prompt(
            "Resume text",
            job_description="Full-stack developer position",
        )

        assert "Resume text" in prompt
        assert "Full-stack developer" in prompt
        assert "Industry Best Practices" not in prompt

    def test_optimize_with_empty_rag_list(self):
        builder = PromptBuilder()
        prompt = builder.build_optimize_prompt(
            "Resume text", retrieved_context=[]
        )
        assert "Industry Best Practices" not in prompt
