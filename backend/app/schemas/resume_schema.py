"""
Resume Schemas

RA-23: Resume upload response (file_id, filename, storage_path)
RA-24: Resume parsing models (extracted structured data)
Design Doc 4.2.1: Unified upload response structure
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    """Contact information extracted from resume"""

    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    location: Optional[str] = Field(None, description="Location/Address")


class Education(BaseModel):
    """Education entry from resume"""

    institution: Optional[str] = Field(None, description="School/University name")
    degree: Optional[str] = Field(None, description="Degree/Qualification")
    field: Optional[str] = Field(None, description="Field of study")
    graduation_year: Optional[str] = Field(None, description="Graduation year")


class WorkExperience(BaseModel):
    """Work experience entry from resume"""

    company: Optional[str] = Field(None, description="Company name")
    position: Optional[str] = Field(None, description="Job title/Position")
    duration: Optional[str] = Field(None, description="Duration (e.g., '2020-2023')")
    description: Optional[str] = Field(None, description="Job responsibilities")


class ResumeData(BaseModel):
    """Parsed resume data structure (RA-24)"""

    full_name: Optional[str] = Field(None, description="Full name of candidate")
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    summary: Optional[str] = Field(None, description="Professional summary")
    skills: List[str] = Field(default_factory=list, description="List of skills")
    education: List[Education] = Field(default_factory=list)
    work_experience: List[WorkExperience] = Field(default_factory=list)
    raw_text: str = Field(..., description="Full extracted text from resume")


class ResumeUploadData(BaseModel):
    """Inner data for resume upload response following Design Doc 4.2.1"""
    session_id: str = Field(..., description="Unique session/file identifier")
    expire_at: str = Field(..., description="ISO timestamp when the session expires")
    filename: Optional[str] = Field(None, description="Original filename")
    storage_path: Optional[str] = Field(None, description="GCS storage path")
    parsed_data: Optional[ResumeData] = Field(None, description="Structured parsed data (RA-24)")


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
