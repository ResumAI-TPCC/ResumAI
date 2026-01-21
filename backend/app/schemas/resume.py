"""
Resume API Pydantic Schemas
"""

from typing import Optional

from pydantic import BaseModel


class ResumeUploadData(BaseModel):
    """Inner data for resume upload response"""
    session_id: str
    expire_at: str


class ResumeUploadResponse(BaseModel):
    """Response schema for resume upload following Design Doc 4.2.1"""
    code: int = 201
    status: str = "ok"
    data: ResumeUploadData


class ResumeAnalyzeRequest(BaseModel):
    """Request schema for resume analysis"""
    session_id: str


class ResumeMatchRequest(BaseModel):
    """Request schema for resume matching"""
    session_id: str
    job_description: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None


class ResumeOptimizeRequest(BaseModel):
    """Request schema for resume optimization"""
    session_id: str
    job_description: Optional[str] = None
    template: str = "modern"
