"""
Resume API Pydantic Schemas
"""

from pydantic import BaseModel
from typing import List

class ResumeUploadResponse(BaseModel):
    """Response schema for resume upload"""

    file_id: str
    filename: str

class ResumeMatchRequest(BaseModel):
    
    resume_content: str  
    job_description: str

class ResumeMatchResponse(BaseModel):
    
    score: float
    suggestions: List[str]