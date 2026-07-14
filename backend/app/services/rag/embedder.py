"""
Gemini embedding adapter used by the RAG retriever.

Backed by langchain-google-genai's GoogleGenerativeAIEmbeddings so the RAG
path shares the same provider stack as the rest of the LLM layer instead of
depending on the standalone google-genai SDK directly.
"""

from typing import Optional

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import settings


class GeminiEmbedder:
    """Small wrapper around the Gemini embedding API."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_EMBEDDING_MODEL
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for RAG embeddings")

        self.client = GoogleGenerativeAIEmbeddings(
            model=self.model,
            google_api_key=self.api_key,
        )

    def embed(self, text: str) -> list[float]:
        """Embed a single non-empty string."""
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        return self.client.embed_query(text.strip())

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple strings in one batch call with deterministic ordering."""
        return self.client.embed_documents([text.strip() for text in texts])
