"""
Mock Interview API Routes
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.core.error_templates import (
    INTERNAL_SERVER_ERROR,
)
from app.schemas.interview_schema import (
    EvaluateAnswerRequest,
    StartInterviewRequest,
)
from app.schemas.resume_schema import JobSubmitData, JobSubmitResponse
from app.services.interview_service import (
    validate_interview_answer_request,
    validate_start_interview_request,
)
from app.services.jobs.job_manager import QueueFullError, get_job_manager

router = APIRouter()


def _queue_full_response() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Queue is full. Please retry later.",
    )


def _submit_job(job_type: str, request) -> JobSubmitResponse:
    job_manager = get_job_manager()
    job_id = job_manager.enqueue(job_type, request)
    return JobSubmitResponse(
        code=202,
        status="ok",
        data=JobSubmitData(
            job_id=job_id,
            job_type=job_type,
            status="pending",
            queue_depth=job_manager.queue_depth,
        ),
    )


@router.post(
    "/start",
    response_model=JobSubmitResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_mock_interview(request: StartInterviewRequest):
    """
    Generate tailored mock interview questions from uploaded resume and JD.
    """
    try:
        await validate_start_interview_request(request)
        return _submit_job("interview_start", request)
    except HTTPException:
        raise
    except QueueFullError:
        raise _queue_full_response()
    except Exception as exc:
        raise HTTPException(
            status_code=INTERNAL_SERVER_ERROR.code,
            detail=INTERNAL_SERVER_ERROR.detail,
        ) from exc


@router.post(
    "/answer",
    response_model=JobSubmitResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def evaluate_mock_interview_answer(request: EvaluateAnswerRequest):
    """
    Evaluate one mock interview answer and return structured feedback.
    """
    try:
        await validate_interview_answer_request(request)
        return _submit_job("interview_answer", request)
    except HTTPException:
        raise
    except QueueFullError:
        raise _queue_full_response()
    except Exception as exc:
        raise HTTPException(
            status_code=INTERNAL_SERVER_ERROR.code,
            detail=INTERNAL_SERVER_ERROR.detail,
        ) from exc
