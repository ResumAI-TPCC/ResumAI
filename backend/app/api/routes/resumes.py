"""
Resume API Routes (RA-82 updated)

/upload          — unchanged, synchronous, returns session_id
/analyze         — async, enqueues job, returns 202 + job_id
/match           — async, enqueues job, returns 202 + job_id
/optimize        — async, enqueues job, returns 202 + job_id

Input validation (session check, empty content, content moderation) still
runs synchronously before enqueue so the queue stays clean and error
responses remain fast.
"""

from __future__ import annotations

from fastapi import APIRouter, File, UploadFile, HTTPException, status

from app.schemas.resume_schema import (
    ResumeAnalyzeRequest,
    ResumeMatchRequest,
    ResumeOptimizeRequest,
    ResumeUploadResponse,
    JobSubmitData,
    JobSubmitResponse,
)
from app.services.resume_service import get_resume_content, upload_resume_to_gcs
from app.services.validators.content_moderator import get_content_moderator
from app.services.jobs.job_manager import get_job_manager, QueueFullError
from app.core.error_templates import (
    RESUME_EMPTY_CONTENT,
    CONTENT_MODERATION_INPUT_BLOCKED,
    INTERNAL_SERVER_ERROR,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _queue_full_response() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Queue is full. Please retry later.",
    )


# ---------------------------------------------------------------------------
# Upload (unchanged — synchronous)
# ---------------------------------------------------------------------------

@router.post("/", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a resume file to GCS and return session information.
    """
    return await upload_resume_to_gcs(file)


# ---------------------------------------------------------------------------
# Analyze
# ---------------------------------------------------------------------------

@router.post("/analyze", response_model=JobSubmitResponse, status_code=status.HTTP_202_ACCEPTED)
async def analyze_resume(request: ResumeAnalyzeRequest):
    """
    Enqueue a resume analysis job and return a job_id for polling.
    """
    try:
        # 1. Fetch and validate resume content before enqueue
        resume_content = await get_resume_content(request.session_id)

        if not resume_content or not resume_content.strip():
            raise HTTPException(
                status_code=RESUME_EMPTY_CONTENT.code,
                detail=RESUME_EMPTY_CONTENT.detail,
            )

        # 2. Content moderation on input
        moderator = get_content_moderator()
        is_safe, reason = moderator.check_input(resume_content)
        if not is_safe:
            raise HTTPException(
                status_code=CONTENT_MODERATION_INPUT_BLOCKED.code,
                detail=reason,
            )

        # 3. Enqueue — fast, non-blocking
        job_manager = get_job_manager()
        job_id = job_manager.enqueue("analyze", request)

        return JobSubmitResponse(
            code=202,
            status="ok",
            data=JobSubmitData(
                job_id=job_id,
                job_type="analyze",
                status="pending",
                queue_depth=job_manager.queue_depth,
            ),
        )

    except HTTPException:
        raise
    except QueueFullError:
        raise _queue_full_response()
    except Exception as e:
        raise HTTPException(
            status_code=INTERNAL_SERVER_ERROR.code,
            detail=INTERNAL_SERVER_ERROR.detail,
        ) from e


# ---------------------------------------------------------------------------
# Match
# ---------------------------------------------------------------------------

@router.post("/match", response_model=JobSubmitResponse, status_code=status.HTTP_202_ACCEPTED)
async def match_resume(request: ResumeMatchRequest):
    """
    Enqueue a resume–JD match job and return a job_id for polling.
    """
    try:
        # 1. Fetch and validate resume content before enqueue
        resume_content = await get_resume_content(request.session_id)

        if not resume_content or not resume_content.strip():
            raise HTTPException(
                status_code=RESUME_EMPTY_CONTENT.code,
                detail=RESUME_EMPTY_CONTENT.detail,
            )

        # 2. Validate that at least one match input is present
        has_jd = bool(request.job_description and request.job_description.strip())
        has_title = bool(request.job_title and request.job_title.strip())
        has_company = bool(request.company_name and request.company_name.strip())

        if not (has_jd or has_title or has_company):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please provide at least one of Job Description, Job Title, or Company Name for matching.",
            )

        # 3. Content moderation on inputs
        moderator = get_content_moderator()
        is_safe, reason = moderator.check_input(resume_content)
        if not is_safe:
            raise HTTPException(
                status_code=CONTENT_MODERATION_INPUT_BLOCKED.code,
                detail=reason,
            )

        if has_jd:
            is_safe, reason = moderator.check_input(request.job_description)
            if not is_safe:
                raise HTTPException(
                    status_code=CONTENT_MODERATION_INPUT_BLOCKED.code,
                    detail=reason,
                )

        # 4. Enqueue
        job_manager = get_job_manager()
        job_id = job_manager.enqueue("match", request)

        return JobSubmitResponse(
            code=202,
            status="ok",
            data=JobSubmitData(
                job_id=job_id,
                job_type="match",
                status="pending",
                queue_depth=job_manager.queue_depth,
            ),
        )

    except HTTPException:
        raise
    except QueueFullError:
        raise _queue_full_response()
    except Exception as e:
        raise HTTPException(
            status_code=INTERNAL_SERVER_ERROR.code,
            detail=INTERNAL_SERVER_ERROR.detail,
        ) from e


# ---------------------------------------------------------------------------
# Optimize
# ---------------------------------------------------------------------------

@router.post("/optimize", response_model=JobSubmitResponse, status_code=status.HTTP_202_ACCEPTED)
async def optimize_resume(request: ResumeOptimizeRequest):
    """
    Enqueue a resume optimization job and return a job_id for polling.
    """
    try:
        # 1. Fetch and validate resume content before enqueue
        resume_content = await get_resume_content(request.session_id)

        if not resume_content or not resume_content.strip():
            raise HTTPException(
                status_code=RESUME_EMPTY_CONTENT.code,
                detail=RESUME_EMPTY_CONTENT.detail,
            )

        # 2. Content moderation on inputs
        moderator = get_content_moderator()
        is_safe, reason = moderator.check_input(resume_content)
        if not is_safe:
            raise HTTPException(
                status_code=CONTENT_MODERATION_INPUT_BLOCKED.code,
                detail=reason,
            )

        if request.job_description:
            is_safe, reason = moderator.check_input(request.job_description)
            if not is_safe:
                raise HTTPException(
                    status_code=CONTENT_MODERATION_INPUT_BLOCKED.code,
                    detail=reason,
                )

        # 3. Enqueue
        job_manager = get_job_manager()
        job_id = job_manager.enqueue("optimize", request)

        return JobSubmitResponse(
            code=202,
            status="ok",
            data=JobSubmitData(
                job_id=job_id,
                job_type="optimize",
                status="pending",
                queue_depth=job_manager.queue_depth,
            ),
        )

    except HTTPException:
        raise
    except QueueFullError:
        raise _queue_full_response()
    except Exception as e:
        raise HTTPException(
            status_code=INTERNAL_SERVER_ERROR.code,
            detail=INTERNAL_SERVER_ERROR.detail,
        ) from e
