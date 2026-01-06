"""
Resume API Routes

RA-12: Basic API endpoints implementation
RA-24: Resume parsing implementation
"""

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from app.schemas.resume import ResumeParseRequest, ResumeParseResponse
from app.services.resume_parser import ResumeParserService

router = APIRouter()


# ============================================================================
# Endpoint 1: Upload & Parse Resume
# ============================================================================
@router.post("/")
async def upload_resume():
    """
    Upload and parse resume file

    Returns:
        dict: Success message with 200 OK
    """
    return {"message": "Resume upload endpoint", "status": "ok"}


# ============================================================================
# Endpoint 1b: Parse Uploaded Resume (RA-24)
# ============================================================================
@router.post("/parse", response_model=ResumeParseResponse)
async def parse_resume(request: ResumeParseRequest):
    """
    Parse an uploaded resume file and extract structured information

    This endpoint takes a file_id and storage_path from the upload endpoint
    and returns extracted resume data including contact info, education,
    work experience, and skills.

    Args:
        request: ResumeParseRequest with file_id and storage_path

    Returns:
        ResumeParseResponse: Parsed resume data

    Raises:
        404: File not found
        400: Unsupported file format or parsing error
        403: Path traversal attempt detected
    """
    # Get backend root - allow override for testing
    backend_root = os.getenv("BACKEND_ROOT")
    if backend_root:
        backend_root = Path(backend_root).resolve()
    else:
        backend_root = Path(__file__).resolve().parents[3]
    
    storage_base = (backend_root / "storage" / "resumes").resolve()

    # Construct and validate file path
    input_path = Path(request.storage_path)
    
    # Convert to absolute path if relative
    if not input_path.is_absolute():
        file_path = (backend_root / request.storage_path).resolve()
    else:
        file_path = input_path.resolve()
    
    # Security: Validate path is within allowed directory
    # This prevents path traversal attacks (../../../etc/passwd)
    try:
        # Check if the resolved path is within storage_base
        file_path.relative_to(storage_base)
    except ValueError:
        # Path is outside allowed directory - could be path traversal attack
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Invalid file path",
        )

    # Verify file exists (safe to use after validation)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume file not found",
        )

    # Extract filename from path
    filename = file_path.name

    # Parse the resume
    try:
        parsed_data = ResumeParserService.parse_file(file_path, filename)

        return ResumeParseResponse(
            file_id=request.file_id,
            filename=filename,
            parsed_data=parsed_data,
            status="success",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse resume: {str(e)}",
        ) from e


# ============================================================================
# Endpoint 2: Calculate Match Score
# ============================================================================
@router.post("/match")
async def match_resume():
    """
    Calculate match score between resume and job description
    
    Returns:
        dict: Success message with 200 OK
    """
    return {"message": "Resume match endpoint", "status": "ok"}


# ============================================================================
# Endpoint 3: Optimize Resume
# ============================================================================
@router.post("/optimize")
async def optimize_resume():
    """
    Optimize resume content
    
    Returns:
        dict: Success message with 200 OK
    """
    return {"message": "Resume optimize endpoint", "status": "ok"}


# ============================================================================
# Endpoint 4: Analyze & Generate Suggestions
# ============================================================================
@router.post("/analyze")
async def analyze_resume():
    """
    Analyze resume and generate improvement suggestions
    
    Returns:
        dict: Success message with 200 OK
    """
    return {"message": "Resume analyze endpoint", "status": "ok"}
