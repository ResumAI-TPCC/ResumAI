"""
Resume API Routes
"""

from __future__ import annotations

from fastapi import APIRouter, File, UploadFile, status

from app.schemas.resume_schema import (
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
    Upload a resume file to GCS and return session information.
    Includes bonus structured data extraction (RA-24).
    """
    return await upload_resume_to_gcs(file)


@router.post("/match")
async def match_resume(request: ResumeMatchRequest):
    """
    Match resume with job description.
    """
    resume_content = await get_resume_content(request.session_id)
    return {
        "message": "Resume match endpoint (Service 1 & 3 ready)",
        "status": "ok",
        "resume_content": resume_content,
        "job_description": request.job_description
    }


@router.post("/optimize")
async def optimize_resume(request: ResumeOptimizeRequest):
    """
    Optimize resume content.
    """
    resume_content = await get_resume_content(request.session_id)
    return {
        "message": "Resume optimize endpoint (Service 1 & 3 ready)",
        "status": "ok",
        "resume_content": resume_content
    }


@router.post("/analyze")
async def analyze_resume(request: ResumeAnalyzeRequest):
    """
    Analyze resume quality.
    """
    resume_content = await get_resume_content(request.session_id)
    return {
        "message": "Resume analyze endpoint (Service 1 & 3 ready)",
        "status": "ok",
        "resume_content": resume_content
    }
