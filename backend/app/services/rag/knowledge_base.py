"""
Curated resume knowledge base backed by ChromaDB.
"""

import logging
from pathlib import Path
from typing import Optional

import chromadb

from .embedder import GeminiEmbedder

logger = logging.getLogger(__name__)

CHROMA_PERSIST_DIR = Path(__file__).resolve().parents[3] / ".chroma_db"
COLLECTION_NAME = "resume_knowledge"

_collection: Optional[chromadb.Collection] = None


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


def reset_knowledge_base() -> None:
    """Reset the in-memory collection handle for tests."""
    global _collection
    _collection = None


def _collection_is_ready(collection: chromadb.Collection) -> bool:
    return collection.count() >= len(KNOWLEDGE_DOCUMENTS)


def build_knowledge_base(
    embedder: Optional[GeminiEmbedder] = None,
    persist_dir: Optional[Path] = None,
    force_rebuild: bool = False,
) -> chromadb.Collection:
    """Build or load the persisted resume knowledge collection."""
    global _collection

    if _collection is not None and not force_rebuild:
        return _collection

    persist_path = persist_dir or CHROMA_PERSIST_DIR
    persist_path.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(persist_path))
    if force_rebuild:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            logger.debug("RAG collection did not exist before force rebuild")

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    if _collection_is_ready(collection) and not force_rebuild:
        _collection = collection
        return collection

    embedder = embedder or GeminiEmbedder()
    ids = [doc["id"] for doc in KNOWLEDGE_DOCUMENTS]
    documents = [doc["content"] for doc in KNOWLEDGE_DOCUMENTS]
    metadatas = [
        {"category": doc["category"], "title": doc["title"]}
        for doc in KNOWLEDGE_DOCUMENTS
    ]

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embedder.embed_batch(documents),
    )
    logger.info("RAG knowledge base ready with %s documents", collection.count())

    _collection = collection
    return collection


def get_collection(persist_dir: Optional[Path] = None) -> Optional[chromadb.Collection]:
    """Load the existing collection without embedding new documents."""
    global _collection

    if _collection is not None:
        return _collection

    persist_path = persist_dir or CHROMA_PERSIST_DIR
    if not persist_path.exists():
        return None

    try:
        client = chromadb.PersistentClient(path=str(persist_path))
        collection = client.get_collection(COLLECTION_NAME)
    except Exception:
        logger.debug("RAG collection is not available yet", exc_info=True)
        return None

    if collection.count() == 0:
        return None

    _collection = collection
    return collection
