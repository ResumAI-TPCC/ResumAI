"""
Resume Schemas

RA-23: Resume upload response (file_id, filename, storage_path)
RA-24: Resume parsing models (extracted structured data)
"""

from typing import Optional

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
    skills: list[str] = Field(default_factory=list, description="List of skills")
    education: list[Education] = Field(default_factory=list)
    work_experience: list[WorkExperience] = Field(default_factory=list)
    raw_text: str = Field(..., description="Full extracted text from resume")


class ResumeUploadData(BaseModel):
    """Inner data for resume upload response"""

    session_id: str = Field(..., description="Session ID (UUID) for the upload")
    expire_at: str = Field(..., description="Expiration timestamp (ISO 8601)")


class ResumeUploadResponse(BaseModel):
    """Response schema for resume upload and parse
    
    Combines RA-23 (GCS upload) and RA-24 (file parsing).
    Always returns code, status, and data containing session_id and other details.
    """

    code: int = Field(201, description="Status code")
    status: str = Field("ok", description="Status message")
    data: ResumeUploadData = Field(..., description="Uploaded resume details")


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
