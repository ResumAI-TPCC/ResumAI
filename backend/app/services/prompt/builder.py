"""
Prompt Builder Service

This module provides the PromptBuilder class for constructing
prompts to send to the LLM service.
"""

from typing import Optional

from .templates import (
    ANALYZE_PROMPT_TEMPLATE,
    OPTIMIZE_NO_JD_PROMPT_TEMPLATE,
    OPTIMIZE_WITH_JD_PROMPT_TEMPLATE,
)


class PromptBuilder:
    """
    Builder class for constructing LLM prompts.

    This class is responsible for taking resume content and other inputs,
    and generating properly formatted prompts for the LLM service.
    """

    def build_analyze_prompt(self, resume_content: str) -> str:
        """
        Build a prompt for resume analysis.

        Args:
            resume_content: The text content of the resume to analyze.

        Returns:
            A formatted prompt string ready to send to the LLM.

        Raises:
            ValueError: If resume_content is empty or contains only whitespace.
        """
        if not resume_content or not resume_content.strip():
            raise ValueError("resume_content cannot be empty")

        return ANALYZE_PROMPT_TEMPLATE.format(
            resume_content=resume_content.strip()
        )

    def build_optimize_prompt(
        self, resume_content: str, job_description: Optional[str] = None
    ) -> str:
        """
        Build a prompt for resume optimization.

        RA-45: Without JD - general optimization for better quality.
        RA-46: With JD - targeted optimization aligned with job description.

        Args:
            resume_content: The text content of the resume to optimize.
            job_description: Optional job description for targeted optimization.

        Returns:
            A formatted prompt string ready to send to the LLM.

        Raises:
            ValueError: If resume_content is empty or contains only whitespace.
        """
        if not resume_content or not resume_content.strip():
            raise ValueError("resume_content cannot be empty")

        if job_description and job_description.strip():
            # RA-46: Optimize with JD
            return OPTIMIZE_WITH_JD_PROMPT_TEMPLATE.format(
                resume_content=resume_content.strip(),
                job_description=job_description.strip(),
            )
        else:
            # RA-45: Optimize without JD
            return OPTIMIZE_NO_JD_PROMPT_TEMPLATE.format(
                resume_content=resume_content.strip()
            )


# Module-level singleton instance
_prompt_builder: Optional[PromptBuilder] = None


def get_prompt_builder() -> PromptBuilder:
    """
    Get the singleton PromptBuilder instance.

    Returns:
        The shared PromptBuilder instance.
    """
    global _prompt_builder
    if _prompt_builder is None:
        _prompt_builder = PromptBuilder()
    return _prompt_builder

