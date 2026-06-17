"""
Semantic retrieval over the resume knowledge base.
"""

import asyncio
import logging
from typing import Optional

from .embedder import GeminiEmbedder
from .knowledge_base import build_knowledge_base, get_collection

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 3


def _sync_retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    embedder: Optional[GeminiEmbedder] = None,
) -> list[str]:
    """Run the blocking ChromaDB query path."""
    if not query or not query.strip():
        return []

    collection = get_collection()
    if collection is None:
        collection = build_knowledge_base(embedder=embedder)

    total_docs = collection.count()
    if total_docs == 0:
        return []

    embedder = embedder or GeminiEmbedder()
    result = collection.query(
        query_embeddings=[embedder.embed(query)],
        n_results=min(top_k, total_docs),
        include=["documents", "metadatas", "distances"],
    )

    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    for metadata, distance in zip(metadatas, distances):
        logger.debug(
            "RAG hit category=%s title=%s distance=%s",
            metadata.get("category"),
            metadata.get("title"),
            distance,
        )

    return [doc for doc in documents if doc]


async def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    embedder: Optional[GeminiEmbedder] = None,
) -> list[str]:
    """Retrieve relevant resume guidance without blocking the event loop."""
    if not query or not query.strip():
        return []

    try:
        return await asyncio.to_thread(_sync_retrieve, query, top_k, embedder)
    except Exception:
        logger.warning("RAG retrieval failed; continuing without context", exc_info=True)
        return []
