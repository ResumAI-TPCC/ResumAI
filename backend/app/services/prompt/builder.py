"""
Prompt Builder Service
Constructs prompts for LLM based on resume content and JD.
"""

import logging
from typing import Optional
from .templates import (
    ANALYZE_PROMPT_TEMPLATE,
    MATCH_PROMPT_TEMPLATE,
    OPTIMIZE_NO_JD_PROMPT_TEMPLATE,
    OPTIMIZE_WITH_JD_PROMPT_TEMPLATE,
    SAFETY_INSTRUCTION,
)

logger = logging.getLogger(__name__)

# Minimum requirements for a meaningful JD
MIN_JD_LENGTH = 20
MIN_JD_ALPHA_RATIO = 0.3


class PromptBuilder:
    """
    Builder class for constructing LLM prompts.
    """

    def build_analyze_prompt(self, resume_content: str) -> str:
        """Build a prompt for resume analysis."""
        if not resume_content or not resume_content.strip():
            raise ValueError("resume_content cannot be empty")

        return ANALYZE_PROMPT_TEMPLATE.format(
            safety_instruction=SAFETY_INSTRUCTION,
            resume_content=resume_content.strip()
        )

    @staticmethod
    def _validate_job_description(job_description: str) -> None:
        """
        Validate that a job description contains meaningful content.

        Rejects JDs that are too short, or consist mostly of numbers/symbols
        rather than actual job-related text.

        Args:
            job_description: The JD text to validate.

        Raises:
            ValueError: If the JD does not meet quality requirements.
        """
        jd = job_description.strip()

        if len(jd) < MIN_JD_LENGTH:
            logger.warning(f"JD rejected: too short ({len(jd)} chars, min {MIN_JD_LENGTH})")
            raise ValueError(
                f"Job description is too short (minimum {MIN_JD_LENGTH} characters). "
                f"Please provide a meaningful job description for accurate matching."
            )

        alpha_count = sum(c.isalpha() for c in jd)
        alpha_ratio = alpha_count / len(jd)
        if alpha_ratio < MIN_JD_ALPHA_RATIO:
            logger.warning(
                f"JD rejected: low alpha ratio ({alpha_ratio:.2f}, min {MIN_JD_ALPHA_RATIO})"
            )
            raise ValueError(
                "Job description does not contain enough meaningful text. "
                "Please provide a real job description with actual words, "
                "not just numbers or symbols."
            )

    def build_match_prompt(self, resume_content: str, job_description: str) -> str:
        """Build a prompt for matching resume with JD."""
        if not resume_content or not resume_content.strip():
            raise ValueError("resume_content cannot be empty")
        if not job_description or not job_description.strip():
            raise ValueError("job_description cannot be empty")

        # Validate JD quality
        self._validate_job_description(job_description)

        return MATCH_PROMPT_TEMPLATE.format(
            safety_instruction=SAFETY_INSTRUCTION,
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
                safety_instruction=SAFETY_INSTRUCTION,
                resume_content=resume_content.strip(),
                job_description=job_description.strip(),
                template=template,
            )
        else:
            # RA-45: Optimize without JD
            return OPTIMIZE_NO_JD_PROMPT_TEMPLATE.format(
                safety_instruction=SAFETY_INSTRUCTION,
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
