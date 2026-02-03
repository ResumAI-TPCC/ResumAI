"""
Resume API Routes

RA-23: Upload resume to GCS
RA-24: Parse resume file and extract structured data
"""

from fastapi import APIRouter, File, UploadFile, status

from app.schemas.resume_schema import (
    ResumeAnalyzeRequest,
    ResumeData,
    ResumeMatchRequest,
    ResumeOptimizeRequest,
    ResumeUploadResponse,
)
from app.services.resume_service import (
    get_resume_content,
    upload_and_parse_resume,
    upload_resume_to_gcs,
)

router = APIRouter()


@router.post("/", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload and optionally parse a resume file.
    
    Handles both RA-23 (GCS upload) and RA-24 (file parsing):
    1. Uploads file to Google Cloud Storage (RA-23)
    2. Attempts to parse file and extract structured data (RA-24)
    
    Returns:
        ResumeUploadResponse:
            - file_id: Session ID from GCS upload (UUID)
            - filename: Original filename
            - storage_path: GCS storage location
            - parsed_data: Extracted resume data (if parsing succeeded)
    
    Raises:
        400: Invalid file format
        413: File too large (>10MB)
        500: GCS upload or server error
    """
    return await upload_and_parse_resume(file)



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
