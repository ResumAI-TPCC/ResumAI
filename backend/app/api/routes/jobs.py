"""
Job Status API Routes - Query Async Job Status

Reads from the new InMemoryJobStore via app.state.job_manager.
"""

from fastapi import APIRouter, HTTPException, Request

from app.schemas.resume_schema import JobStatusResponse, JobStatusData

router = APIRouter()


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, req: Request):
    """
    Get job status and result by job_id.

    Returns:
        - queued: Job is waiting to be processed
        - processing: Job is currently being executed
        - completed: Job finished successfully, result included
        - failed: Job failed, error message included
    """
    record = req.app.state.job_manager.get_job(job_id)

    if record is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    return JobStatusResponse(
        code=200,
        status="ok",
        data=JobStatusData(
            job_id=record.job_id,
            status=record.status.value,
            task_type=record.payload.task_type,
            created_at=record.created_at,
            updated_at=record.updated_at,
            result=record.result,
            error=record.error,
        ),
    )
