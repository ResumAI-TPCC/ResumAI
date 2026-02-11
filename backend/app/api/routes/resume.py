"""
Resume API Routes

RA-23: Upload resume to GCS
RA-24: Parse resume file and extract structured data
RA-45: Optimize resume without JD
RA-46: Optimize resume with JD
RA-47: Download optimized resume as base64 encoded file
"""

from fastapi import APIRouter, File, UploadFile, status
from fastapi.responses import Response

from app.schemas.optimize_schema import OptimizeRequest, OptimizeResponse
from app.schemas.resume_schema import ResumeDownloadRequest, ResumeUploadResponse
from app.services.resume_service import (
    download_resume,
    optimize_resume as optimize_resume_service,
    upload_and_parse_resume,
)

router = APIRouter()


@router.post("/", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload and optionally parse a resume file.
    
    Handles both RA-23 (GCS upload) and RA-24 (file parsing):
    1. Uploads file to Google Cloud Storage (RA-23)
    2. Attempts to parse file and extract structured data (RA-24)
    """
    return await upload_and_parse_resume(file)


@router.post("/download")
async def download_resume_file(request: ResumeDownloadRequest):
    """
    Download processed resume file from storage.
    """
    content, content_type, filename = await download_resume(
        file_id=request.file_id,
        storage_path=request.storage_path,
    )
    
    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize_resume_endpoint(request: OptimizeRequest):
    """
    Optimize resume and return base64 encoded Markdown file (RA-45/46/47).
    
    - Without job_description (RA-45): General optimization for quality
    - With job_description (RA-46): Targeted optimization for specific role
    - Returns base64 encoded file for download (RA-47)
    
    Args:
        request: OptimizeRequest with session_id and optional job_description
        
    Returns:
        OptimizeResponse with encoded_file (base64), filename, and format
    """
    return await optimize_resume_service(
        session_id=request.session_id,
        job_description=request.job_description,
    )


@router.post("/match")
async def match_resume():
    """Calculate match score between resume and job description"""
    return {"message": "Resume match endpoint", "status": "ok"}


@router.post("/analyze")
async def analyze_resume():
    """Analyze resume and generate improvement suggestions"""
    return {"message": "Resume analyze endpoint", "status": "ok"}
