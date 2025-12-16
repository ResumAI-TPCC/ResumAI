"""
Chat-related Pydantic Schema Definitions
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Chat message"""

    role: Literal["system", "user", "assistant"] = Field(
        description="Message role"
    )
    content: str = Field(description="Message content")


class ChatRequest(BaseModel):
    """Chat request"""

    messages: List[ChatMessage] = Field(
        description="List of messages",
        min_length=1,
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature parameter, controls output randomness",
    )
    max_tokens: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum number of tokens to generate",
    )
    stream: bool = Field(
        default=False,
        description="Whether to use streaming response",
    )


class ChatResponse(BaseModel):
    """Chat response"""

    content: str = Field(description="Response content")
    model: str = Field(description="Model used")
    usage: Optional[dict] = Field(default=None, description="Token usage statistics")

