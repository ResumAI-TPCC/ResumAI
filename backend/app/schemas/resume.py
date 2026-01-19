"""
Resume API Pydantic Schemas
"""

from pydantic import BaseModel


class ResumeUploadResponse(BaseModel):
    """Response schema for resume upload"""

    file_id: str
    filename: str
