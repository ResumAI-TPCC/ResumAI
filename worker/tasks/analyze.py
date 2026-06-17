"""
Worker Task: Analyze Resume

Business logic extracted from the old Celery task.
Called by any runner (LocalBackgroundRunner, future CeleryRunner, etc.)
"""

from __future__ import annotations

import asyncio
import logging

from app.services.resume_service import get_resume_content
from app.services.prompt.builder import get_prompt_builder
from app.services.llm.llm_service import get_llm_service
from app.services.validators.content_moderator import get_content_moderator
from app.services.jobs.schemas import JobPayload

logger = logging.getLogger(__name__)


def run_analyze_job(payload: JobPayload) -> dict:
    """
    Execute resume analysis and return result dict.

    Args:
        payload: JobPayload with session_id in arguments

    Returns:
        {"suggestions": [...]}

    Raises:
        ValueError: on empty content or moderation failure
    """
    session_id: str = payload.arguments["session_id"]

    resume_content = asyncio.run(get_resume_content(session_id))
    if not resume_content or not resume_content.strip():
        raise ValueError("Resume content is empty")

    moderator = get_content_moderator()
    is_safe, reason = moderator.check_input(resume_content)
    if not is_safe:
        raise ValueError(f"Content moderation blocked: {reason}")

    prompt = get_prompt_builder().build_analyze_prompt(resume_content)
    result = asyncio.run(get_llm_service().analyze_resume(prompt))

    return {
        "suggestions": [
            {
                "category": s.category,
                "priority": s.priority,
                "title": s.title,
                "description": s.description,
                "example": s.example or "N/A",
            }
            for s in result.suggestions
        ]
    }
