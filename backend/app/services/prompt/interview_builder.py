"""
Interview Prompt Builder

Builds prompts for mock interview question generation.
"""

from __future__ import annotations

from typing import Optional

from app.services.prompt.interview_templates import (
    INTERVIEW_QUESTION_GENERATION_TEMPLATE,
)
from app.services.prompt.templates import SAFETY_INSTRUCTION


class InterviewPromptBuilder:
    """Constructs prompts for mock interview workflows."""

    def build_question_generation_prompt(
        self,
        resume_content: str,
        job_description: str,
        job_title: Optional[str] = None,
        company_name: Optional[str] = None,
        question_count: int = 5,
    ) -> str:
        """Build a prompt that asks the LLM to generate interview questions."""
        if not resume_content or not resume_content.strip():
            raise ValueError("resume_content cannot be empty")
        if not job_description or not job_description.strip():
            raise ValueError("job_description cannot be empty")

        return INTERVIEW_QUESTION_GENERATION_TEMPLATE.format(
            safety_instruction=SAFETY_INSTRUCTION,
            resume_content=resume_content.strip(),
            job_description=job_description.strip(),
            job_title=(job_title or "N/A").strip() or "N/A",
            company_name=(company_name or "N/A").strip() or "N/A",
            question_count=question_count,
        )


_interview_prompt_builder: Optional[InterviewPromptBuilder] = None


def get_interview_prompt_builder() -> InterviewPromptBuilder:
    """Get the singleton InterviewPromptBuilder instance."""
    global _interview_prompt_builder
    if _interview_prompt_builder is None:
        _interview_prompt_builder = InterviewPromptBuilder()
    return _interview_prompt_builder
