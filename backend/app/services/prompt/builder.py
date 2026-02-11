"""
Prompt Builder Service
Constructs prompts for LLM based on resume content and JD.
"""

from typing import Optional
from .templates import (
    ANALYZE_PROMPT_TEMPLATE,
    MATCH_PROMPT_TEMPLATE,
    OPTIMIZE_NO_JD_PROMPT_TEMPLATE,
    OPTIMIZE_WITH_JD_PROMPT_TEMPLATE,
)


class PromptBuilder:
    """
    Builder class for constructing LLM prompts.
    """

    def build_analyze_prompt(self, resume_content: str) -> str:
        """Build a prompt for resume analysis."""
        if not resume_content or not resume_content.strip():
            raise ValueError("resume_content cannot be empty")

        return ANALYZE_PROMPT_TEMPLATE.format(
            resume_content=resume_content.strip()
        )

    def build_match_prompt(self, resume_content: str, job_description: str) -> str:
        """Build a prompt for matching resume with JD."""
        if not resume_content or not resume_content.strip():
            raise ValueError("resume_content cannot be empty")
        if not job_description or not job_description.strip():
            raise ValueError("job_description cannot be empty")

        return MATCH_PROMPT_TEMPLATE.format(
            resume_content=resume_content.strip(),
            job_description=job_description.strip()
        )

    def build_optimize_prompt(self, resume_content: str, job_description: Optional[str] = None, template: str = "modern") -> str:
        """
        Build a prompt for resume optimization.

        RA-45: Without JD - general optimization for better quality.
        RA-46: With JD - targeted optimization aligned with job description.
        """
        if not resume_content or not resume_content.strip():
            raise ValueError("resume_content cannot be empty")

        if job_description and job_description.strip():
            # RA-46: Optimize with JD
            return OPTIMIZE_WITH_JD_PROMPT_TEMPLATE.format(
                resume_content=resume_content.strip(),
                job_description=job_description.strip(),
                template=template,
            )
        else:
            # RA-45: Optimize without JD
            return OPTIMIZE_NO_JD_PROMPT_TEMPLATE.format(
                resume_content=resume_content.strip(),
                template=template,
            )


# Singleton instance
_prompt_builder: Optional[PromptBuilder] = None


def get_prompt_builder() -> PromptBuilder:
    """Get the singleton PromptBuilder instance."""
    global _prompt_builder
    if _prompt_builder is None:
        _prompt_builder = PromptBuilder()
    return _prompt_builder
