"""
Curated resume knowledge base with in-memory embeddings.

Uses Gemini embeddings + numpy cosine similarity. Avoids ChromaDB/onnxruntime
so CI (Python 3.10) and Cloud Run (512Mi) stay lean for a 10-document seed set.
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

from .embedder import GeminiEmbedder

logger = logging.getLogger(__name__)

PERSIST_DIR = Path(__file__).resolve().parents[3] / ".rag_store"
STORE_FILENAME = "resume_knowledge.json"

_store: Optional["KnowledgeStore"] = None
_store_lock = threading.Lock()

KNOWLEDGE_DOCUMENTS = [
    {
        "id": "structure-001",
        "category": "structure",
        "title": "Resume Section Order",
        "content": (
            "Use a predictable resume structure: contact information, professional "
            "summary, work experience, skills, education, and optional projects or "
            "certifications. Keep the most relevant sections near the top. Avoid "
            "photos, full mailing addresses, and personal details that do not help "
            "a recruiter evaluate role fit."
        ),
    },
    {
        "id": "content-001",
        "category": "content",
        "title": "Quantified Achievements",
        "content": (
            "Strong resume bullets describe measurable business or technical impact. "
            "Prefer action plus scope plus result, such as reduced API latency from "
            "800ms to 120ms, supported 45k monthly active users, or cut cloud spend "
            "by 30 percent. Quantify at least half of the experience bullets when "
            "credible numbers are available."
        ),
    },
    {
        "id": "language-001",
        "category": "language",
        "title": "Action Verb Quality",
        "content": (
            "Begin bullets with specific action verbs such as architected, shipped, "
            "automated, refactored, migrated, deployed, scaled, debugged, or reduced. "
            "Avoid weak openers like responsible for, helped with, worked on, and "
            "assisted in because they hide ownership and impact."
        ),
    },
    {
        "id": "ats-001",
        "category": "ats",
        "title": "ATS Keyword Strategy",
        "content": (
            "Applicant tracking systems reward clear headings and exact keyword "
            "matches. Use standard headings like Work Experience, Skills, Education, "
            "and Projects. Mirror job description terminology honestly, spell out "
            "acronyms at first use, and avoid tables, text boxes, images, and "
            "header-only content that parsers can miss."
        ),
    },
    {
        "id": "skills-001",
        "category": "skills",
        "title": "Technical Skills Section",
        "content": (
            "Keep the skills section compact and grouped by type: Languages, "
            "Frameworks, Cloud and Infrastructure, Databases, and Tools. List only "
            "skills the candidate can discuss in an interview. Move role-critical "
            "technical keywords near the top for engineering and data resumes."
        ),
    },
    {
        "id": "summary-001",
        "category": "content",
        "title": "Professional Summary",
        "content": (
            "A useful professional summary is two to four lines and states the "
            "candidate's role, years or depth of experience, core domain, and "
            "strongest evidence of impact. Avoid generic phrases like results-driven "
            "or passionate unless they are backed by concrete outcomes."
        ),
    },
    {
        "id": "experience-001",
        "category": "content",
        "title": "Experience Bullet Format",
        "content": (
            "Work experience bullets should follow context, action, result. Lead "
            "with the most relevant and highest-impact accomplishments in each role. "
            "A strong bullet names the system or process improved, the technology or "
            "method used, and the measurable outcome."
        ),
    },
    {
        "id": "jd-alignment-001",
        "category": "matching",
        "title": "Tailoring To A Job Description",
        "content": (
            "For a targeted resume, identify required skills, tools, responsibilities, "
            "seniority signals, and domain terms in the job description. Add missing "
            "keywords only when truthful, reorder bullets toward the target role, and "
            "adapt the summary to the role's most important requirements."
        ),
    },
    {
        "id": "format-001",
        "category": "format",
        "title": "Formatting Consistency",
        "content": (
            "Consistent formatting improves scanning speed. Use one date format, "
            "consistent bullet punctuation, readable spacing, and a small set of "
            "heading styles. Do not shrink margins excessively or pack unrelated "
            "details into dense paragraphs."
        ),
    },
    {
        "id": "education-001",
        "category": "education",
        "title": "Education And Certifications",
        "content": (
            "Place education near the top for early-career candidates and near the "
            "bottom for experienced candidates. Include institution, degree, field, "
            "and graduation year when useful. List active, role-relevant "
            "certifications separately with issuer and date."
        ),
    },
]


@dataclass
class KnowledgeStore:
    """In-memory resume guidance corpus with precomputed embeddings."""

    documents_hash: str
    ids: list[str]
    documents: list[str]
    metadatas: list[dict]
    embeddings: np.ndarray

    def count(self) -> int:
        return len(self.documents)

    def query(
        self,
        query_embedding: list[float],
        top_k: int = 3,
    ) -> tuple[list[str], list[dict], list[float]]:
        """Return top-k documents by cosine similarity (higher is better)."""
        if self.count() == 0:
            return [], [], []

        query = np.asarray(query_embedding, dtype=np.float64)
        query_norm = np.linalg.norm(query)
        if query_norm == 0:
            return [], [], []

        matrix = self.embeddings
        doc_norms = np.linalg.norm(matrix, axis=1)
        valid = doc_norms > 0
        scores = np.zeros(len(matrix), dtype=np.float64)
        scores[valid] = (matrix[valid] @ query) / (doc_norms[valid] * query_norm)

        k = min(top_k, self.count())
        top_indices = np.argsort(-scores)[:k]
        documents = [self.documents[i] for i in top_indices]
        metadatas = [self.metadatas[i] for i in top_indices]
        # Distance-style metric for logging (1 - cosine), matching prior Chroma habit
        distances = [float(1.0 - scores[i]) for i in top_indices]
        return documents, metadatas, distances


def compute_documents_hash() -> str:
    """Stable hash of the curated document set."""
    payload = [
        {
            "id": doc["id"],
            "category": doc["category"],
            "title": doc["title"],
            "content": doc["content"],
        }
        for doc in KNOWLEDGE_DOCUMENTS
    ]
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def reset_knowledge_base() -> None:
    """Reset the in-memory store handle for tests."""
    global _store
    with _store_lock:
        _store = None


def _store_path(persist_dir: Path) -> Path:
    return persist_dir / STORE_FILENAME


def _store_is_valid(store: KnowledgeStore) -> bool:
    return (
        store.count() == len(KNOWLEDGE_DOCUMENTS)
        and store.documents_hash == compute_documents_hash()
    )


def _load_store(persist_dir: Path) -> Optional[KnowledgeStore]:
    path = _store_path(persist_dir)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        store = KnowledgeStore(
            documents_hash=payload["documents_hash"],
            ids=payload["ids"],
            documents=payload["documents"],
            metadatas=payload["metadatas"],
            embeddings=np.asarray(payload["embeddings"], dtype=np.float64),
        )
    except Exception:
        logger.debug("RAG store file could not be loaded", exc_info=True)
        return None

    if not _store_is_valid(store):
        logger.debug(
            "RAG store ignored (count=%s, hash=%s)",
            store.count(),
            store.documents_hash,
        )
        return None
    return store


def _save_store(store: KnowledgeStore, persist_dir: Path) -> None:
    persist_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "documents_hash": store.documents_hash,
        "ids": store.ids,
        "documents": store.documents,
        "metadatas": store.metadatas,
        "embeddings": store.embeddings.tolist(),
    }
    _store_path(persist_dir).write_text(
        json.dumps(payload),
        encoding="utf-8",
    )


def build_knowledge_base(
    embedder: Optional[GeminiEmbedder] = None,
    persist_dir: Optional[Path] = None,
    force_rebuild: bool = False,
) -> KnowledgeStore:
    """Build or load the resume knowledge store."""
    global _store

    with _store_lock:
        if _store is not None and not force_rebuild and _store_is_valid(_store):
            return _store

        target_dir = persist_dir or PERSIST_DIR
        if not force_rebuild:
            loaded = _load_store(target_dir)
            if loaded is not None:
                _store = loaded
                return loaded

        embedder = embedder or GeminiEmbedder()
        ids = [doc["id"] for doc in KNOWLEDGE_DOCUMENTS]
        documents = [doc["content"] for doc in KNOWLEDGE_DOCUMENTS]
        metadatas = [
            {"category": doc["category"], "title": doc["title"]}
            for doc in KNOWLEDGE_DOCUMENTS
        ]
        embeddings = np.asarray(
            embedder.embed_batch(documents),
            dtype=np.float64,
        )

        store = KnowledgeStore(
            documents_hash=compute_documents_hash(),
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        _save_store(store, target_dir)
        logger.info("RAG knowledge base ready with %s documents", store.count())
        _store = store
        return store


def get_store(persist_dir: Optional[Path] = None) -> Optional[KnowledgeStore]:
    """Load an existing store without embedding new documents."""
    global _store

    with _store_lock:
        if _store is not None and _store_is_valid(_store):
            return _store

        target_dir = persist_dir or PERSIST_DIR
        loaded = _load_store(target_dir)
        if loaded is None:
            return None
        _store = loaded
        return loaded


# Backwards-compatible alias used by older call sites / tests.
get_collection = get_store
