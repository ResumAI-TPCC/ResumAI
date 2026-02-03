"""
Resume API Routes
"""

from __future__ import annotations

from fastapi import APIRouter, File, UploadFile, status

from app.schemas.resume import (
    ResumeAnalyzeRequest,
    ResumeMatchRequest,
    ResumeOptimizeRequest,
    ResumeUploadResponse,
)
from app.services.resume_service import get_resume_content, upload_resume_to_gcs

router = APIRouter()


@router.post("/", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a resume file.
    Returns 201 Created on success with file_id.
    """
    return await upload_resume_to_gcs(file)


@router.post("/match")
async def match_resume(request: ResumeMatchRequest):
    resume_content = await get_resume_content(request.session_id)
    return {
        "message": "Resume match endpoint (Service 1 integrated)",
        "status": "ok",
        "resume_content": resume_content,
        "job_description": request.job_description
    }


@router.post("/optimize")
async def optimize_resume(request: ResumeOptimizeRequest):
    resume_content = await get_resume_content(request.session_id)
    return {
        "message": "Resume optimize endpoint (Service 1 integrated)",
        "status": "ok",
        "resume_content": resume_content
    }


@router.post("/analyze")
async def analyze_resume(request: ResumeAnalyzeRequest):
    resume_content = await get_resume_content(request.session_id)
    return {
        "message": "Resume analyze endpoint (Service 1 integrated)",
        "status": "ok",
        "resume_content": resume_content
    }
