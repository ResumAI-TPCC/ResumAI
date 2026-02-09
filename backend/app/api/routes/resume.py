"""
Resume API Routes

RA-23: Upload resume to GCS
RA-24: Parse resume file and extract structured data
RA-47: Download processed resume file
"""

from fastapi import APIRouter, File, UploadFile, status
from fastapi.responses import Response

from app.schemas.resume_schema import ResumeDownloadRequest, ResumeUploadResponse
from app.services.resume_service import download_resume, upload_and_parse_resume

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


@router.post("/download")
async def download_resume_file(request: ResumeDownloadRequest):
    """
    Download processed resume file from storage (RA-47).
    
    This endpoint allows users to download a previously uploaded resume file
    from Google Cloud Storage using the file_id and storage_path.
    
    Args:
        request: ResumeDownloadRequest with file_id and storage_path
        
    Returns:
        File content with appropriate media type headers
        
    Raises:
        400: Invalid storage path format
        404: File not found
        500: Download or server error
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


@router.post("/match")
async def match_resume():
    """Calculate match score between resume and job description"""
    return {"message": "Resume match endpoint", "status": "ok"}


@router.post("/optimize")
async def optimize_resume():
    """Optimize resume content"""
    return {"message": "Resume optimize endpoint", "status": "ok"}


@router.post("/analyze")
async def analyze_resume():
    """Analyze resume and generate improvement suggestions"""
    return {"message": "Resume analyze endpoint", "status": "ok"}
