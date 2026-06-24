"""
Jobs API Routes (RA-82)

Provides the polling endpoint for frontend to check async job status and retrieve results.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas.resume_schema import JobStatusData, JobStatusResponse
from app.services.jobs.job_manager import get_job_manager
from app.services.jobs.result_manager import get_result_manager

router = APIRouter()


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Poll the status and result of an async job.

    - **pending**: Job is waiting in the queue.
    - **processing**: A worker has picked up the job and is calling the LLM.
    - **completed**: Result is ready; `data.result` contains the payload.
    - **failed**: LLM or processing error; `data.error` contains the message.

    Returns 404 if the job_id is unknown or the result has expired (TTL = 30 min).
    """
    result_manager = get_result_manager()
    entry = result_manager.get(job_id)

    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or result has expired.",
        )

    job_manager = get_job_manager()

    return JobStatusResponse(
        code=200,
        status="ok",
        data=JobStatusData(
            job_id=entry["job_id"],
            job_type=entry["job_type"],
            status=entry["status"],
            result=entry["result"],
            error=entry["error"],
            queue_depth=job_manager.queue_depth,
        ),
    )
