"""
RAG helpers for resume analysis.
"""

from .knowledge_base import KNOWLEDGE_DOCUMENTS, build_knowledge_base, get_collection
from .retriever import retrieve

__all__ = [
    "KNOWLEDGE_DOCUMENTS",
    "build_knowledge_base",
    "get_collection",
    "retrieve",
]
