"""
Resume API Routes
"""

import time
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException, status

from app.schemas.resume import ResumeUploadResponse
from app.services.resume_service import parse_file_from_bytes

router = APIRouter()


@router.post("/", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(..., description="Resume file (PDF, DOCX, or TXT)")
):
    """
    Upload and parse resume file
    
    Accepts PDF, DOCX, or TXT files and extracts structured resume data including:
    - Contact information (email, phone, LinkedIn, GitHub)
    - Personal summary
    - Skills
    - Work experience
    - Education
    - Projects
    - Languages
    - Certifications
    
    Args:
        file: Resume file to parse
    
    Returns:
        ResumeUploadResponse: Parsed resume data with metadata
    
    Raises:
        400: Unsupported file format
        422: File parsing failed
        500: Internal server error
    """
    start_time = time.time()
    
    # Validate file size (10MB limit)
    max_file_size = 10 * 1024 * 1024
    file_content = await file.read()
    
    if len(file_content) > max_file_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {max_file_size // (1024 * 1024)}MB"
        )
    
    # Detect file type from extension
    file_ext = '.' + file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    
    if file_ext not in ['.pdf', '.docx', '.txt']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format: {file_ext}. Supported formats: PDF, DOCX, TXT"
        )
    
    # Security: Extract only the basename to prevent path traversal
    safe_filename = Path(file.filename).name
    if ".." in safe_filename or safe_filename.startswith(("/", "\\")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename"
        )
    
    try:
        parsed_data = await parse_file_from_bytes(
            file_content=file_content,
            filename=safe_filename,
            file_type=file.content_type
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return ResumeUploadResponse(
            success=True,
            message="Resume parsed successfully",
            data=parsed_data,
            file_type=file_ext.lstrip('.'),
            processing_time_ms=processing_time
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format or content"
        )
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        print(f"Resume parsing error: {str(e)}")
        
        return ResumeUploadResponse(
            success=False,
            message="Failed to parse resume",
            data=None,
            file_type=file_ext.lstrip('.'),
            processing_time_ms=processing_time,
            error="An error occurred while processing the file"
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
