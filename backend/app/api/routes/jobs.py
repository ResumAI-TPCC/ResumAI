"""
Job Status API Routes - Query Async Job Status

Provides endpoint to poll job status and retrieve results.
"""

from fastapi import APIRouter, HTTPException

from app.schemas.resume_schema import JobStatusResponse, JobStatusData
from app.services.queue.job_store import get_job_store, JobStatus

router = APIRouter()


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get job status and result by job_id.
    
    Returns:
        - queued: Job is waiting to be processed
        - processing: Job is currently being executed
        - completed: Job finished successfully, result included
        - failed: Job failed, error message included
    """
    job_store = get_job_store()
    job_data = job_store.get_job(job_id)
    
    if job_data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}"
        )
    
    return JobStatusResponse(
        code=200,
        status="ok",
        data=JobStatusData(
            job_id=job_data["job_id"],
            status=job_data["status"],
            task_type=job_data["task_type"],
            created_at=job_data["created_at"],
            updated_at=job_data["updated_at"],
            result=job_data.get("result"),
            error=job_data.get("error"),
        )
    )
