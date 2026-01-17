"""
Resume API Routes
"""

from __future__ import annotations

from fastapi import APIRouter, File, UploadFile

from app.services.resume_service import upload_resume_to_gcs

router = APIRouter()


@router.post("/")
async def upload_resume(file: UploadFile = File(...)):
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