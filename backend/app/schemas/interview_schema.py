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


class ScoringBreakdown(BaseModel):
    """Rubric scores for evaluating a single interview answer."""

    relevance: int = Field(
        ...,
        ge=0,
        le=30,
        description="Relevance to the question and JD, max 30",
    )
    specificity: int = Field(
        ...,
        ge=0,
        le=25,
        description="Use of resume/JD evidence and concrete details, max 25",
    )
    structure: int = Field(
        ...,
        ge=0,
        le=20,
        description="Answer organization and clarity, max 20",
    )
    impact: int = Field(
        ...,
        ge=0,
        le=15,
        description="Outcomes, metrics, and business or technical impact, max 15",
    )
    communication: int = Field(
        ...,
        ge=0,
        le=10,
        description="Conciseness, professionalism, and reflection, max 10",
    )


class EvaluateAnswerRequest(BaseModel):
    """Request body for evaluating one mock interview answer."""

    interview_id: str
    session_id: str
    question_id: str
    question_type: str
    question: str
    resume_evidence: Optional[str] = None
    jd_evidence: Optional[str] = None
    focus_areas: List[str] = Field(default_factory=list)
    answer: str
    job_description: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None


class EvaluateAnswerData(BaseModel):
    """Structured feedback for one interview answer."""

    question_id: str
    score: int = Field(..., ge=0, le=100)
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    improved_answer: str
    jd_alignment: str
    scoring_breakdown: ScoringBreakdown


class EvaluateAnswerResponse(BaseModel):
    """Response for evaluating one mock interview answer."""

    code: int = 200
    status: str = "ok"
    data: EvaluateAnswerData
