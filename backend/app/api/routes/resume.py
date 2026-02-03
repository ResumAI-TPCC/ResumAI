"""
Resume API Routes
"""

from __future__ import annotations

from fastapi import APIRouter, File, UploadFile, status, HTTPException

from app.schemas.resume import ResumeUploadResponse, ResumeMatchRequest, ResumeMatchResponse
from app.services.resume_service import upload_resume_to_gcs
from app.services.llm.gemini import GeminiProvider

router = APIRouter()
gemini_provider = GeminiProvider()


@router.post("/", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a resume file.
    Returns 201 Created on success with file_id.
    """
    return await upload_resume_to_gcs(file)


@router.post("/match", response_model=ResumeMatchResponse)
async def match_resume(request: ResumeMatchRequest):
    try:
        result = await gemini_provider.match(
            resume_content=request.resume_content,
            job_description=request.job_description
        )

        if not result.get("success", False):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", {}).get("message", "Unknown error")
            )
        return result
 
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"LLM Processing Error: {str(e)}"
        )


@router.post("/optimize")
async def optimize_resume(request: ResumeMatchRequest):
    result = await gemini_provider.optimize(
        resume_content=request.resume_content,
        job_description=request.job_description
    )
    return {"optimized_content": result.content, "usage": result.usage}


@router.post("/analyze")
async def analyze_resume(request: ResumeMatchRequest):
    result = await gemini_provider.analyze(
        resume_content=request.resume_content,
        job_description=request.job_description
    )
    return {"analysis": result.content, "usage": result.usage}