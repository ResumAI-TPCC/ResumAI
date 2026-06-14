"""
Interview Schemas

Schemas for Phase 1 text-based mock interview question generation.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class InterviewQuestion(BaseModel):
    """Single generated mock interview question."""

    id: str = Field(..., description="Stable question id, e.g. q1")
    type: str = Field(
        ...,
        description="Question type, e.g. self_intro or resume_based",
    )
    label: str = Field(..., description="Human-readable question type label")
    question: str = Field(..., description="Interview question text")
    resume_evidence: Optional[str] = Field(
        default=None,
        description="Concrete resume detail used to personalize the question",
    )
    jd_evidence: Optional[str] = Field(
        default=None,
        description="Concrete JD or company detail used to personalize the question",
    )
    focus_areas: List[str] = Field(
        default_factory=list,
        description="What the interviewer is evaluating",
    )


class StartInterviewRequest(BaseModel):
    """Request body for starting a mock interview."""

    session_id: str
    job_description: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    question_count: int = Field(default=5, ge=5, le=5)


class StartInterviewData(BaseModel):
    """Inner data for start interview response."""

    interview_id: str
    questions: List[InterviewQuestion]


class StartInterviewResponse(BaseModel):
    """Response for starting a mock interview."""

    code: int = 200
    status: str = "ok"
    data: StartInterviewData
