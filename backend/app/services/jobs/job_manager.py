"""
Job Manager (RA-82)

Async job queue backed by asyncio.Queue.

Design decisions:
- Single worker coroutine (serial processing) for MVP:
    * Simplest implementation — no asyncio.Lock needed on ResultManager.
    * Gemini calls are async I/O; the worker awaits without blocking FastAPI's
      event loop, so /upload and GET /jobs/{id} remain fully responsive
      during LLM processing.
    * Avoids Gemini rate-limit (ResourceExhausted) storms that would occur
      with multiple concurrent workers all retrying with backoff.
    * Scaling to N workers later only requires changing MAX_WORKERS in config
      and starting multiple tasks — no other files need to change.
- Queue capacity enforced via asyncio.Queue(maxsize=MAX_QUEUE_SIZE).
  Queue-full → caller receives HTTP 429 (checked before put_nowait).
- Worker is started during FastAPI lifespan startup and cancelled on shutdown.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from app.core.config import settings
from app.services.jobs.result_manager import get_result_manager

logger = logging.getLogger(__name__)

# Valid job types
JOB_TYPES = frozenset({"analyze", "match", "optimize"})


@dataclass
class Job:
    """A single unit of work placed on the queue."""
    job_id: str
    job_type: str          # "analyze" | "match" | "optimize"
    payload: Any           # The validated request object (ResumeAnalyzeRequest, etc.)


class JobManager:
    """
    Manages the async job queue and the single worker coroutine.

    Lifecycle (called from FastAPI lifespan in main.py):
        await job_manager.start()   # on startup
        await job_manager.stop()    # on shutdown
    """

    def __init__(self, max_queue_size: int | None = None):
        size = max_queue_size if max_queue_size is not None else settings.MAX_QUEUE_SIZE
        self._queue: asyncio.Queue[Job] = asyncio.Queue(maxsize=size)
        self._worker_task: asyncio.Task | None = None
        self._result_manager = get_result_manager()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the background worker coroutine. Called once on app startup."""
        if self._worker_task is not None and not self._worker_task.done():
            logger.warning("JobManager worker is already running.")
            return
        self._worker_task = asyncio.create_task(self._worker(), name="job-worker")
        logger.info("JobManager worker started.")

    async def stop(self) -> None:
        """Cancel the background worker. Called once on app shutdown."""
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("JobManager worker stopped.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def enqueue(self, job_type: str, payload: Any) -> str:
        """
        Add a job to the queue and return its job_id.

        Args:
            job_type: One of "analyze", "match", "optimize"
            payload:  The validated request object from the route handler

        Returns:
            job_id (str): UUID4 string

        Raises:
            QueueFullError: If the queue has reached MAX_QUEUE_SIZE
        """
        if self._queue.full():
            raise QueueFullError(
                f"Queue is full ({settings.MAX_QUEUE_SIZE} jobs). Please retry later."
            )

        job_id = str(uuid.uuid4())
        job = Job(job_id=job_id, job_type=job_type, payload=payload)

        # put_nowait is safe here because we checked full() above.
        # Both checks happen in the same synchronous frame (no await between
        # them), so there is no race condition in a single-threaded asyncio loop.
        self._queue.put_nowait(job)
        self._result_manager.create(job_id, job_type)

        logger.info(
            f"Job enqueued: {job_id} ({job_type}), queue_depth={self.queue_depth}"
        )
        return job_id

    @property
    def queue_depth(self) -> int:
        """Number of jobs currently waiting in the queue (not including in-flight)."""
        return self._queue.qsize()

    # ------------------------------------------------------------------
    # Worker
    # ------------------------------------------------------------------

    async def _worker(self) -> None:
        """
        Continuously dequeues and processes jobs until cancelled.

        Imports llm_service lazily inside the loop to avoid circular imports
        and to reuse the existing lru_cache singleton.
        """
        # Lazy import to avoid circular dependency at module load time
        from app.services.llm.llm_service import get_llm_service
        from app.services.prompt.builder import get_prompt_builder
        from app.services.resume_service import get_resume_content

        logger.info("Job worker loop started.")
        while True:
            try:
                job: Job = await self._queue.get()
                logger.info(f"Worker picked up job: {job.job_id} ({job.job_type})")
                self._result_manager.set_processing(job.job_id)

                try:
                    result = await self._execute_job(job, get_llm_service, get_prompt_builder, get_resume_content)
                    self._result_manager.set_completed(job.job_id, result)
                except Exception as exc:
                    logger.error(
                        f"Job {job.job_id} failed: {exc}", exc_info=True
                    )
                    self._result_manager.set_failed(job.job_id, str(exc))
                finally:
                    self._queue.task_done()

            except asyncio.CancelledError:
                logger.info("Job worker received cancellation signal.")
                break
            except Exception as exc:
                # Unexpected error in the worker loop itself — log and continue
                logger.error(f"Unexpected worker loop error: {exc}", exc_info=True)

        logger.info("Job worker loop exited.")

    async def _execute_job(self, job: Job, get_llm_service, get_prompt_builder, get_resume_content) -> dict:
        """
        Dispatch to the appropriate LLM service method based on job_type.

        Mirrors the logic previously inline in each route handler, but without
        HTTP concerns — raises plain exceptions on failure (worker catches them).

        Returns a plain dict matching the original endpoint's `data` field shape,
        so GET /jobs/{job_id} can return it directly.
        """
        from app.services.validators.content_moderator import get_content_moderator, ContentModerationError
        from app.services.pdf_service import markdown_to_pdf
        import base64

        payload = job.payload
        llm = get_llm_service()
        builder = get_prompt_builder()

        # ---- Retrieve resume content (common to all job types) ----
        resume_content = await get_resume_content(payload.session_id)

        if not resume_content or not resume_content.strip():
            raise ValueError("Resume content is empty.")

        moderator = get_content_moderator()

        if job.job_type == "analyze":
            is_safe, reason = moderator.check_input(resume_content)
            if not is_safe:
                raise ContentModerationError(reason)

            prompt = builder.build_analyze_prompt(resume_content)
            result = await llm.analyze_resume(prompt)

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

        elif job.job_type == "match":
            has_jd = bool(payload.job_description and payload.job_description.strip())
            has_title = bool(payload.job_title and payload.job_title.strip())
            has_company = bool(payload.company_name and payload.company_name.strip())

            if has_jd:
                match_context = payload.job_description.strip()
            elif has_title or has_company:
                match_context = (
                    "Target role context:\n"
                    f"Company: {(payload.company_name or '').strip() or 'N/A'}\n"
                    f"Job Title: {(payload.job_title or '').strip() or 'N/A'}\n"
                    "Use this context to evaluate resume-job fit."
                )
            else:
                raise ValueError(
                    "Please provide at least one of Job Description, Job Title, or Company Name for matching."
                )

            for text in (resume_content, match_context):
                is_safe, reason = moderator.check_input(text)
                if not is_safe:
                    raise ContentModerationError(reason)

            prompt = builder.build_match_prompt(resume_content, match_context)
            result = await llm.match_resume(prompt)

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

        elif job.job_type == "optimize":
            is_safe, reason = moderator.check_input(resume_content)
            if not is_safe:
                raise ContentModerationError(reason)

            if payload.job_description:
                is_safe, reason = moderator.check_input(payload.job_description)
                if not is_safe:
                    raise ContentModerationError(reason)

            prompt = builder.build_optimize_prompt(
                resume_content,
                payload.job_description,
                payload.template,
            )
            result = await llm.optimize_resume(prompt)

            pdf_bytes = markdown_to_pdf(result.optimized_content)
            encoded_content = base64.b64encode(pdf_bytes).decode()

            return {"encoded_file": encoded_content}

        else:
            raise ValueError(f"Unknown job type: {job.job_type}")


class QueueFullError(Exception):
    """Raised by JobManager.enqueue() when the queue has reached capacity."""


@lru_cache
def get_job_manager() -> JobManager:
    """Return the singleton JobManager instance."""
    return JobManager()
