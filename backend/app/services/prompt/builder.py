"""
Prompt Builder Service

Provides job-description validation used before calling the match chain.
Prompt construction itself is handled by the ChatPromptTemplate objects in
templates.py, which are composed directly into LangChain LCEL chains inside
LLMService.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Minimum requirements for a meaningful JD
MIN_JD_LENGTH = 20
MIN_JD_ALPHA_RATIO = 0.3


class PromptBuilder:
    """
    Validates inputs before they reach the LLM chains.

    Prompt assembly is now owned by LLMService via ChatPromptTemplate;
    this class retains only input-quality validation so callers have a
    stable import path.
    """

    @staticmethod
    def validate_job_description(job_description: str) -> None:
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
                "Please provide a meaningful job description for accurate matching."
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


# Singleton instance
_prompt_builder: Optional[PromptBuilder] = None


def get_prompt_builder() -> PromptBuilder:
    """Get the singleton PromptBuilder instance."""
    global _prompt_builder
    if _prompt_builder is None:
        _prompt_builder = PromptBuilder()
    return _prompt_builder
