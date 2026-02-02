"""
Resume API Routes
"""

from __future__ import annotations

import base64

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas.resume import (
    OptimizeData,
    OptimizeRequest,
    OptimizeResponse,
    ResumeUploadResponse,
)
from app.services.llm import get_llm_provider
from app.services.resume_service import get_resume_text, upload_resume_to_gcs

router = APIRouter()


@router.post("/", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a resume file.
    Returns 201 Created on success with file_id.
    """
    return await upload_resume_to_gcs(file)


@router.post("/match")
async def match_resume():
    return {"message": "Resume match endpoint", "status": "ok"}


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize_resume(request: OptimizeRequest):
    """
    Optimize resume using AI.

    - Service 1 (No JD): General optimization when job_description is not provided
    - Service 2 (With JD): JD-specific optimization when job_description is provided

    Args:
        request: OptimizeRequest with session_id and optional job_description

    Returns:
        OptimizeResponse: { code, status, data: { encoded_file } }

    Raises:
        400: Invalid parameters
        404: Resume not found
        500: Server error
    """
    # Validate session_id
    if not request.session_id or not request.session_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id is required and cannot be empty",
        )

    try:
        # 1. Get resume text content from GCS (download + parse)
        resume_content = await get_resume_text(request.session_id.strip())

        # 2. Get LLM provider and optimize
        provider = get_llm_provider()
        result = await provider.optimize(
            resume_content=resume_content,
            job_description=request.job_description or "",
        )

        # 3. Encode the optimized content as base64
        encoded_file = base64.b64encode(result.content.encode("utf-8")).decode("utf-8")

        # 4. Return response in standard format
        return OptimizeResponse(
            code=200,
            status="ok",
            data=OptimizeData(encoded_file=encoded_file),
        )

    except HTTPException:
        # Re-raise HTTP exceptions (400, 404, etc.)
        raise
    except Exception as exc:
        # Catch any unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization failed: {str(exc)}",
        ) from exc


@router.post("/analyze")
async def analyze_resume():
    return {"message": "Resume analyze endpoint", "status": "ok"}
