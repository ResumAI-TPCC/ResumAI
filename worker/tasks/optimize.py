"""
Worker Task: Optimize Resume

Business logic extracted from the old Celery task.
"""

from __future__ import annotations

import asyncio
import base64
import logging

from app.services.resume_service import get_resume_content
from app.services.pdf_service import markdown_to_pdf
from app.services.prompt.builder import get_prompt_builder
from app.services.llm.llm_service import get_llm_service
from app.services.validators.content_moderator import get_content_moderator
from app.services.jobs.schemas import JobPayload

logger = logging.getLogger(__name__)


def run_optimize_job(payload: JobPayload) -> dict:
    """
    Execute resume optimization and return base64-encoded PDF.

    Args:
        payload: JobPayload with session_id, job_description (opt),
                 template (opt) in arguments

    Returns:
        {"encoded_file": "<base64 string>"}

    Raises:
        ValueError: on empty content or moderation failure
    """
    args = payload.arguments
    session_id: str = args["session_id"]
    job_description: str = args.get("job_description", "")
    template: str = args.get("template", "modern")

    resume_content = asyncio.run(get_resume_content(session_id))
    if not resume_content or not resume_content.strip():
        raise ValueError("Resume content is empty")

    moderator = get_content_moderator()
    is_safe, reason = moderator.check_input(resume_content)
    if not is_safe:
        raise ValueError(f"Content moderation blocked: {reason}")

    if job_description:
        is_safe, reason = moderator.check_input(job_description)
        if not is_safe:
            raise ValueError(f"Content moderation blocked: {reason}")

    prompt = get_prompt_builder().build_optimize_prompt(
        resume_content, job_description or None, template
    )
    result = asyncio.run(get_llm_service().optimize_resume(prompt))

    pdf_bytes = markdown_to_pdf(result.optimized_content)
    return {"encoded_file": base64.b64encode(pdf_bytes).decode()}
