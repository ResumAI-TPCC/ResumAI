"""
Resume API Pydantic Schemas
"""

from typing import Optional

from pydantic import BaseModel, Field


# ============================================================================
# Upload Schemas
# ============================================================================


class ResumeUploadResponse(BaseModel):
    """Response schema for resume upload"""

    file_id: str
    filename: str


# ============================================================================
# Optimize Schemas
# ============================================================================


class OptimizeRequest(BaseModel):
    """
    Request schema for resume optimization.

    Attributes:
        session_id: The session/file ID returned from upload
        job_description: Target job description (optional for general optimization)
        template: Resume template style (optional, default: "modern")
    """

    session_id: str = Field(..., description="Session ID from resume upload")
    job_description: Optional[str] = Field(
        None, description="Target job description for JD-specific optimization"
    )
    template: Optional[str] = Field(
        "modern", description="Resume template style"
    )


class OptimizeData(BaseModel):
    """Data payload for optimization response."""

    encoded_file: str = Field(..., description="Base64 encoded optimized resume")


class OptimizeResponse(BaseModel):
    """
    Response schema for resume optimization.

    Follows the standard API response format:
    {
        "code": 200,
        "status": "ok",
        "data": { "encoded_file": "..." }
    }
    """

    code: int = Field(200, description="HTTP status code")
    status: str = Field("ok", description="Response status")
    data: OptimizeData = Field(..., description="Response data payload")
