"""
Optimize Resume Schemas
"""

from typing import Optional

from pydantic import BaseModel, Field


class OptimizeRequest(BaseModel):
    """Request schema for resume optimization"""

    session_id: str = Field(..., description="Session ID from upload")
    job_description: Optional[str] = Field(None, description="Optional job description")


class OptimizeResponse(BaseModel):
    """Response schema for optimized resume download"""

    encoded_file: str = Field(..., description="Base64 encoded file content")
    filename: str = Field(..., description="Suggested filename")
    format: str = Field(default="markdown", description="File format")
