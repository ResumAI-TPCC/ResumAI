"""
Interview Prompt Builder

Builds prompts for mock interview question generation.
"""

from __future__ import annotations

from typing import Optional

from app.services.prompt.interview_templates import (
    INTERVIEW_ANSWER_EVALUATION_TEMPLATE,
    INTERVIEW_QUESTION_GENERATION_TEMPLATE,
)
from app.services.prompt.templates import SAFETY_INSTRUCTION


class InterviewPromptBuilder:
    """Constructs prompts for mock interview workflows."""

    def validate_question_generation_inputs(
        self,
        resume_content: str,
        job_description: str,
    ) -> None:
        """Validate question-generation inputs without formatting the prompt."""
        if not resume_content or not resume_content.strip():
            raise ValueError("resume_content cannot be empty")
        if not job_description or not job_description.strip():
            raise ValueError("job_description cannot be empty")

    def validate_answer_evaluation_inputs(
        self,
        resume_content: str,
        job_description: str,
        question: str,
        answer: str,
    ) -> None:
        """Validate answer-evaluation inputs without formatting the prompt."""
        if not resume_content or not resume_content.strip():
            raise ValueError("resume_content cannot be empty")
        if not job_description or not job_description.strip():
            raise ValueError("job_description cannot be empty")
        if not question or not question.strip():
            raise ValueError("question cannot be empty")
        if not answer or not answer.strip():
            raise ValueError("answer cannot be empty")

    def build_question_generation_prompt(
        self,
        resume_content: str,
        job_description: str,
        job_title: Optional[str] = None,
        company_name: Optional[str] = None,
        question_count: int = 5,
    ) -> str:
        """Build a prompt that asks the LLM to generate interview questions."""
        self.validate_question_generation_inputs(resume_content, job_description)

        return INTERVIEW_QUESTION_GENERATION_TEMPLATE.format(
            safety_instruction=SAFETY_INSTRUCTION,
            resume_content=resume_content.strip(),
            job_description=job_description.strip(),
            job_title=(job_title or "N/A").strip() or "N/A",
            company_name=(company_name or "N/A").strip() or "N/A",
            question_count=question_count,
        )

    def build_answer_evaluation_prompt(
        self,
        resume_content: str,
        job_description: str,
        question_id: str,
        question_type: str,
        question: str,
        answer: str,
        resume_evidence: Optional[str] = None,
        jd_evidence: Optional[str] = None,
        focus_areas: Optional[list[str]] = None,
        job_title: Optional[str] = None,
        company_name: Optional[str] = None,
    ) -> str:
        """Build a prompt that asks the LLM to evaluate one answer."""
        self.validate_answer_evaluation_inputs(
            resume_content,
            job_description,
            question,
            answer,
        )

        normalized_focus_areas = ", ".join(
            area.strip()
            for area in focus_areas or []
            if area and area.strip()
        )

        return INTERVIEW_ANSWER_EVALUATION_TEMPLATE.format(
            safety_instruction=SAFETY_INSTRUCTION,
            resume_content=resume_content.strip(),
            job_description=job_description.strip(),
            job_title=(job_title or "N/A").strip() or "N/A",
            company_name=(company_name or "N/A").strip() or "N/A",
            question_id=(question_id or "N/A").strip() or "N/A",
            question_type=(question_type or "N/A").strip() or "N/A",
            question=question.strip(),
            resume_evidence=(resume_evidence or "N/A").strip() or "N/A",
            jd_evidence=(jd_evidence or "N/A").strip() or "N/A",
            focus_areas=normalized_focus_areas or "N/A",
            answer=answer.strip(),
        )


_interview_prompt_builder: Optional[InterviewPromptBuilder] = None


def get_interview_prompt_builder() -> InterviewPromptBuilder:
    """Get the singleton InterviewPromptBuilder instance."""
    global _interview_prompt_builder
    if _interview_prompt_builder is None:
        _interview_prompt_builder = InterviewPromptBuilder()
    return _interview_prompt_builder
