"""
Resume Schemas
RA-24: Resume parsing data models
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
    """Parsed resume data structure"""

    full_name: Optional[str] = Field(None, description="Full name of candidate")
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    summary: Optional[str] = Field(None, description="Professional summary")
    skills: list[str] = Field(default_factory=list, description="List of skills")
    education: list[Education] = Field(default_factory=list)
    work_experience: list[WorkExperience] = Field(default_factory=list)
    raw_text: str = Field(..., description="Full extracted text from resume")


class ResumeUploadResponse(BaseModel):
    """Response schema for resume upload and parse"""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    data: Optional[ResumeData] = Field(None, description="Parsed resume data")
    file_type: str = Field(..., description="File type (pdf, docx, txt)")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    error: Optional[str] = Field(None, description="Error message if failed")
