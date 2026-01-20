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


class ResumeUploadResponse(BaseModel):
    """Response schema for resume upload and parse
    
    Combines RA-23 (GCS upload) and RA-24 (file parsing).
    Always returns file_id/session_id from upload.
    Returns parsed_data only if parsing was successful.
    """

    # RA-23: Upload info (always present)
    file_id: str = Field(..., description="File ID (UUID) from GCS upload")
    filename: str = Field(..., description="Original filename")
    storage_path: str = Field(..., description="GCS storage path (gs://bucket/...)")
    
    # RA-24: Parsing info (optional, only if parsing succeeded)
    parsed_data: Optional[ResumeData] = Field(None, description="Parsed resume data (RA-24)")
