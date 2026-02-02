"""
Resume API Routes

RA-23: Upload resume to GCS
RA-24: Parse resume file and extract structured data
RA-47: Download optimized resume
"""

from fastapi import APIRouter, File, UploadFile, status

from app.schemas.optimize_schema import OptimizeRequest, OptimizeResponse
from app.schemas.resume_schema import ResumeUploadResponse
from app.services.file_service import generate_and_encode_resume
from app.services.resume_service import upload_and_parse_resume

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
async def match_resume():
    """Calculate match score between resume and job description"""
    return {"message": "Resume match endpoint", "status": "ok"}


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize_resume(request: OptimizeRequest):
    """
    Generate optimized resume file for download
    
    RA-47: File generation and download (current implementation)
    RA-45/46: LLM optimization (to be integrated)
    
    Args:
        request: Contains session_id and optional job_description
        
    Returns:
        Base64 encoded file ready for download
    """
    # TODO (RA-45/46): Replace with actual LLM optimization
    # For now, use placeholder content to test download functionality
    
    optimized_content = f"""# Resume

## Professional Summary
Experienced professional with strong background in software development.

## Skills
- Python, FastAPI
- React, JavaScript
- Cloud platforms (GCP)

## Experience
**Software Engineer**
- Built scalable web applications
- Improved system performance by 40%

---
*Session: {request.session_id}*
*Optimized: {"with JD" if request.job_description else "without JD"}*
"""
    
    encoded_file = generate_and_encode_resume(optimized_content)
    
    return OptimizeResponse(
        encoded_file=encoded_file,
        filename="optimized_resume.md",
        format="markdown"
    )


@router.post("/analyze")
async def analyze_resume():
    """Analyze resume and generate improvement suggestions"""
    return {"message": "Resume analyze endpoint", "status": "ok"}
