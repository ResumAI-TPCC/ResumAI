"""
Semantic retrieval over the resume knowledge base.
"""

import asyncio
import logging
from typing import Optional

from app.core.config import settings

from .embedder import GeminiEmbedder
from .knowledge_base import build_knowledge_base, get_store

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 3

# gemini-embedding-001 caps the number of input tokens per request. Bound the
# query well under that limit (~4 chars/token) so a long, multi-page resume
# never overflows the embedding input and silently loses retrieval.
MAX_QUERY_CHARS = 8000


def _sync_retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    embedder: Optional[GeminiEmbedder] = None,
) -> list[str]:
    """Run the blocking retrieval path (numpy cosine similarity)."""
    if not query or not query.strip():
        return []

    store = get_store()
    if store is None:
        store = build_knowledge_base(embedder=embedder)

    if store.count() == 0:
        return []

    embed_query = query.strip()
    if len(embed_query) > MAX_QUERY_CHARS:
        logger.info(
            "RAG query truncated from %d to %d chars before embedding",
            len(embed_query),
            MAX_QUERY_CHARS,
        )
        embed_query = embed_query[:MAX_QUERY_CHARS]

    embedder = embedder or GeminiEmbedder()
    documents, metadatas, distances = store.query(
        query_embedding=embedder.embed(embed_query),
        top_k=min(top_k, store.count()),
    )

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
    timeout_seconds: Optional[float] = None,
) -> list[str]:
    """Retrieve relevant resume guidance without blocking the event loop.

    Embedding stalls must not block the serial job-queue worker: wrap the
    sync path in ``asyncio.wait_for`` and degrade to no context on timeout.
    """
    if not query or not query.strip():
        return []

    timeout = (
        settings.RAG_RETRIEVAL_TIMEOUT_SECONDS
        if timeout_seconds is None
        else timeout_seconds
    )

    try:
        results = await asyncio.wait_for(
            asyncio.to_thread(_sync_retrieve, query, top_k, embedder),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        logger.warning(
            "RAG retrieval timed out after %.1fs; continuing without context",
            timeout,
        )
        return []
    except Exception:
        logger.warning("RAG retrieval failed; continuing without context", exc_info=True)
        return []

    if results:
        logger.info("RAG retrieved %d snippet(s) for analysis", len(results))
    else:
        logger.warning(
            "RAG returned no context; analysis will run without retrieved guidance"
        )

    return results
