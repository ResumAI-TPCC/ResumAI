"""
Resume API Routes
"""

from __future__ import annotations

from fastapi import APIRouter, File, UploadFile, status

from app.schemas.resume import ResumeUploadResponse
from app.services.resume_service import upload_resume_to_gcs

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


@router.post("/optimize")
async def optimize_resume():
    return {"message": "Resume optimize endpoint", "status": "ok"}


@router.post("/analyze")
async def analyze_resume():
    return {"message": "Resume analyze endpoint", "status": "ok"}
