"""
Prompt Builder Service

Assembles ChatPromptTemplate messages for each LLM operation and validates
inputs before they reach the provider.

build_*_prompt() methods return List[BaseMessage] (formatted LangChain
messages) instead of a raw string, so the provider can pass them directly
to ChatGoogleGenerativeAI.ainvoke() without any further wrapping.
"""

import logging
from typing import List, Optional

from langchain_core.messages import BaseMessage

from .templates import (
    ANALYZE_PROMPT,
    MATCH_PROMPT,
    OPTIMIZE_NO_JD_PROMPT,
    OPTIMIZE_WITH_JD_PROMPT,
)

logger = logging.getLogger(__name__)

# Minimum requirements for a meaningful JD
MIN_JD_LENGTH = 20
MIN_JD_ALPHA_RATIO = 0.3


class PromptBuilder:
    """
    Builds LangChain message lists for each resume operation.

    Each build_*_prompt() method:
    1. Validates inputs
    2. Calls the corresponding ChatPromptTemplate.format_messages()
    3. Returns List[BaseMessage] ready for provider.ainvoke()
    """

    def build_analyze_prompt(self, resume_content: str) -> List[BaseMessage]:
        """Build messages for resume analysis."""
        if not resume_content or not resume_content.strip():
            raise ValueError("resume_content cannot be empty")

        return ANALYZE_PROMPT.format_messages(
            resume_content=resume_content.strip()
        )

    def build_match_prompt(
        self, resume_content: str, job_description: str
    ) -> List[BaseMessage]:
        """Build messages for resume–JD matching."""
        if not resume_content or not resume_content.strip():
            raise ValueError("resume_content cannot be empty")
        if not job_description or not job_description.strip():
            raise ValueError("job_description cannot be empty")

        self.validate_job_description(job_description)

        return MATCH_PROMPT.format_messages(
            resume_content=resume_content.strip(),
            job_description=job_description.strip(),
        )

    def build_optimize_prompt(
        self,
        resume_content: str,
        job_description: Optional[str] = None,
        template: str = "modern",
    ) -> List[BaseMessage]:
        """
        Build messages for resume optimization.

        RA-45: Without JD — general optimization for better quality.
        RA-46: With JD — targeted optimization aligned with job description.
        """
        if not resume_content or not resume_content.strip():
            raise ValueError("resume_content cannot be empty")

        if job_description and job_description.strip():
            return OPTIMIZE_WITH_JD_PROMPT.format_messages(
                resume_content=resume_content.strip(),
                job_description=job_description.strip(),
                template=template,
            )
        else:
            return OPTIMIZE_NO_JD_PROMPT.format_messages(
                resume_content=resume_content.strip(),
                template=template,
            )

    @staticmethod
    def validate_job_description(job_description: str) -> None:
        """
        Validate that a job description contains meaningful content.

        Rejects JDs that are too short, or consist mostly of numbers/symbols
        rather than actual job-related text.

        Raises:
            ValueError: If the JD does not meet quality requirements.
        """
        jd = job_description.strip()

        if len(jd) < MIN_JD_LENGTH:
            logger.warning(
                f"JD rejected: too short ({len(jd)} chars, min {MIN_JD_LENGTH})"
            )
            raise ValueError(
                f"Job description is too short (minimum {MIN_JD_LENGTH} characters). "
                "Please provide a meaningful job description for accurate matching."
            )

        alpha_count = sum(c.isalpha() for c in jd)
        alpha_ratio = alpha_count / len(jd)
        if alpha_ratio < MIN_JD_ALPHA_RATIO:
            logger.warning(
                f"JD rejected: low alpha ratio ({alpha_ratio:.2f}, "
                f"min {MIN_JD_ALPHA_RATIO})"
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
