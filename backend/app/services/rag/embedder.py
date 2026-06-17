"""
Gemini embedding adapter used by the RAG retriever.
"""

from typing import Optional

from google import genai

from app.core.config import settings


class GeminiEmbedder:
    """Small wrapper around the Gemini embedding API."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_EMBEDDING_MODEL
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for RAG embeddings")

        self.client = genai.Client(api_key=self.api_key)

    def embed(self, text: str) -> list[float]:
        """Embed a single non-empty string."""
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        result = self.client.models.embed_content(
            model=self.model,
            contents=text.strip(),
        )
        return list(result.embeddings[0].values)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple strings with deterministic ordering."""
        return [self.embed(text) for text in texts]
