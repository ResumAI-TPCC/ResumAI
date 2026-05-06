"""
Celery Tasks - Background Job Processing

Implements async tasks for resume analysis, matching, and optimization.
"""

import logging
from typing import Optional

from .celery_app import celery_app
from .job_store import JobStatus, get_job_store

from app.services.resume_service import get_resume_content
from app.services.pdf_service import markdown_to_pdf
from app.services.prompt.builder import get_prompt_builder
from app.services.llm.llm_service import get_llm_service
from app.services.validators.content_moderator import get_content_moderator

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_task(self, job_id: str, session_id: str):
    """
    Async task: Analyze resume quality.
    
    Args:
        job_id: Unique job identifier
        session_id: Session ID for resume retrieval
    """
    job_store = get_job_store()
    
    try:
        # Update status to processing
        job_store.update_status(job_id, JobStatus.PROCESSING)
        
        # Get resume content (sync wrapper for async function)
        import asyncio
        resume_content = asyncio.run(get_resume_content(session_id))
        
        if not resume_content or not resume_content.strip():
            raise ValueError("Resume content is empty")
        
        # Content moderation - check input
        moderator = get_content_moderator()
        is_safe, reason = moderator.check_input(resume_content)
        if not is_safe:
            raise ValueError(f"Content moderation blocked: {reason}")
        
        # Build prompt and call LLM
        builder = get_prompt_builder()
        prompt = builder.build_analyze_prompt(resume_content)
        
        llm = get_llm_service()
        result = asyncio.run(llm.analyze_resume(prompt))
        
        # Build response
        suggestions = [
            {
                "category": s.category,
                "priority": s.priority,
                "title": s.title,
                "description": s.description,
                "example": s.example or "N/A",
            }
            for s in result.suggestions
        ]
        
        result_data = {"suggestions": suggestions}
        
        # Save result
        job_store.set_result(job_id, result_data)
        
        return result_data
        
    except Exception as e:
        logger.exception(f"Analyze task {job_id} failed")
        job_store.set_error(job_id, str(e))
        raise self.retry(exc=e)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def match_task(
    self,
    job_id: str,
    session_id: str,
    job_description: str,
    job_title: Optional[str] = None,
    company_name: Optional[str] = None,
):
    """
    Async task: Match resume with job description.
    
    Args:
        job_id: Unique job identifier
        session_id: Session ID for resume retrieval
        job_description: Job description text
        job_title: Optional job title
        company_name: Optional company name
    """
    job_store = get_job_store()
    
    try:
        # Update status to processing
        job_store.update_status(job_id, JobStatus.PROCESSING)
        
        # Get resume content
        import asyncio
        resume_content = asyncio.run(get_resume_content(session_id))
        
        if not resume_content or not resume_content.strip():
            raise ValueError("Resume content is empty")
        
        # Build match context
        has_job_description = bool(job_description and job_description.strip())
        has_job_title = bool(job_title and job_title.strip())
        has_company_name = bool(company_name and company_name.strip())
        
        if has_job_description:
            match_context = job_description.strip()
        elif has_job_title or has_company_name:
            match_context = (
                "Target role context:\n"
                f"Company: {(company_name or '').strip() or 'N/A'}\n"
                f"Job Title: {(job_title or '').strip() or 'N/A'}\n"
                "Use this context to evaluate resume-job fit."
            )
        else:
            raise ValueError(
                "Please provide at least one of Job Description, Job Title, or Company Name."
            )
        
        # Content moderation
        moderator = get_content_moderator()
        is_safe, reason = moderator.check_input(resume_content)
        if not is_safe:
            raise ValueError(f"Content moderation blocked: {reason}")
        
        is_safe, reason = moderator.check_input(match_context)
        if not is_safe:
            raise ValueError(f"Content moderation blocked: {reason}")
        
        # Build prompt and call LLM
        builder = get_prompt_builder()
        prompt = builder.build_match_prompt(resume_content, match_context)
        
        llm = get_llm_service()
        result = asyncio.run(llm.match_resume(prompt))
        
        # Build response
        result_data = {
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
        
        # Save result
        job_store.set_result(job_id, result_data)
        
        return result_data
        
    except Exception as e:
        logger.exception(f"Match task {job_id} failed")
        job_store.set_error(job_id, str(e))
        raise self.retry(exc=e)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def optimize_task(
    self,
    job_id: str,
    session_id: str,
    job_description: Optional[str] = None,
    template: str = "modern",
):
    """
    Async task: Optimize resume content.
    
    Args:
        job_id: Unique job identifier
        session_id: Session ID for resume retrieval
        job_description: Optional job description for targeted optimization
        template: Template name (default: modern)
    """
    job_store = get_job_store()
    
    try:
        # Update status to processing
        job_store.update_status(job_id, JobStatus.PROCESSING)
        
        # Get resume content
        import asyncio
        resume_content = asyncio.run(get_resume_content(session_id))
        
        if not resume_content or not resume_content.strip():
            raise ValueError("Resume content is empty")
        
        # Content moderation
        moderator = get_content_moderator()
        is_safe, reason = moderator.check_input(resume_content)
        if not is_safe:
            raise ValueError(f"Content moderation blocked: {reason}")
        
        if job_description:
            is_safe, reason = moderator.check_input(job_description)
            if not is_safe:
                raise ValueError(f"Content moderation blocked: {reason}")
        
        # Build prompt and call LLM
        builder = get_prompt_builder()
        prompt = builder.build_optimize_prompt(
            resume_content, job_description, template
        )
        
        llm = get_llm_service()
        result = asyncio.run(llm.optimize_resume(prompt))
        
        # Convert to PDF and encode
        import base64
        pdf_bytes = markdown_to_pdf(result.optimized_content)
        encoded_content = base64.b64encode(pdf_bytes).decode()
        
        result_data = {"encoded_file": encoded_content}
        
        # Save result
        job_store.set_result(job_id, result_data)
        
        return result_data
        
    except Exception as e:
        logger.exception(f"Optimize task {job_id} failed")
        job_store.set_error(job_id, str(e))
        raise self.retry(exc=e)
