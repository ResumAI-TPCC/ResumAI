"""
Worker Task: Match Resume with Job Description

Business logic extracted from the old Celery task.
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


def run_match_job(payload: JobPayload) -> dict:
    """
    Execute resume-JD matching and return result dict.

    Args:
        payload: JobPayload with session_id, job_description,
                 job_title (opt), company_name (opt) in arguments

    Returns:
        {"match_score": int, "match_breakdown": {...}, "suggestions": [...]}

    Raises:
        ValueError: on empty content, missing JD context, or moderation failure
    """
    args = payload.arguments
    session_id: str = args["session_id"]
    job_description: str = args.get("job_description", "")
    job_title: str = args.get("job_title", "")
    company_name: str = args.get("company_name", "")

    resume_content = asyncio.run(get_resume_content(session_id))
    if not resume_content or not resume_content.strip():
        raise ValueError("Resume content is empty")

    # Build match context (same logic as sync route)
    if job_description and job_description.strip():
        match_context = job_description.strip()
    elif job_title or company_name:
        match_context = (
            "Target role context:\n"
            f"Company: {company_name.strip() or 'N/A'}\n"
            f"Job Title: {job_title.strip() or 'N/A'}\n"
            "Use this context to evaluate resume-job fit."
        )
    else:
        raise ValueError(
            "Please provide at least one of Job Description, Job Title, or Company Name."
        )

    moderator = get_content_moderator()
    for text in (resume_content, match_context):
        is_safe, reason = moderator.check_input(text)
        if not is_safe:
            raise ValueError(f"Content moderation blocked: {reason}")

    prompt = get_prompt_builder().build_match_prompt(resume_content, match_context)
    result = asyncio.run(get_llm_service().match_resume(prompt))

    return {
        "match_score": result.match_score,
        "match_breakdown": {
            "skills_match": result.match_breakdown.skills_match,
            "experience_match": result.match_breakdown.experience_match,
            "education_match": result.match_breakdown.education_match,
            "keywords_match": result.match_breakdown.keywords_match,
        },
        "suggestions": [
            {
                "category": s.category,
                "priority": s.priority,
                "title": s.title,
                "description": s.description,
                "action": s.action or "N/A",
            }
            for s in result.suggestions
        ],
    }
