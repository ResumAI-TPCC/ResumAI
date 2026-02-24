"""
Resume API Routes
"""

from __future__ import annotations

import base64
from fastapi import APIRouter, File, UploadFile, status

from app.schemas.resume_schema import (
    ResumeAnalyzeRequest,
    ResumeAnalyzeResponse,
    ResumeMatchRequest,
    ResumeMatchResponse,
    ResumeOptimizeRequest,
    ResumeOptimizeResponse,
    ResumeUploadResponse,
    AnalyzeResponseData,
    AnalyzeSuggestion,
    MatchResponseData,
    MatchBreakdown,
    MatchSuggestion,
    OptimizeResponseData,
)
from app.services.resume_service import get_resume_content, upload_resume_to_gcs
from app.services.prompt.builder import get_prompt_builder
from app.services.llm.llm_service import get_llm_service
from app.services.pdf_service import markdown_to_pdf, markdown_to_html

router = APIRouter()


@router.post("/", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a resume file to GCS and return session information.
    """
    return await upload_resume_to_gcs(file)


@router.post("/analyze", response_model=ResumeAnalyzeResponse)
async def analyze_resume(request: ResumeAnalyzeRequest):
    """
    Analyze resume quality using LLM.
    """
    # 1. Get resume text content (Service 1)
    resume_content = await get_resume_content(request.session_id)

    # 2. Build prompt (Service 2)
    builder = get_prompt_builder()
    prompt = builder.build_analyze_prompt(resume_content)

    # 3. Call LLM and parse result (Service 3)
    llm = get_llm_service()
    result = await llm.analyze_resume(prompt)

    # 4. Map to API response schema
    suggestions = [
        AnalyzeSuggestion(
            category=s.category,
            priority=s.priority,
            title=s.title,
            description=s.description,
            example=s.example or "N/A"
        )
        for s in result.suggestions
    ]

    return ResumeAnalyzeResponse(
        code=200,
        status="ok",
        data=AnalyzeResponseData(suggestions=suggestions)
    )


@router.post("/match", response_model=ResumeMatchResponse)
async def match_resume(request: ResumeMatchRequest):
    """
    Match resume with job description using LLM.
    """
    # 1. Get resume content (Service 1)
    resume_content = await get_resume_content(request.session_id)

    # 2. Build match prompt (Service 2)
    builder = get_prompt_builder()
    prompt = builder.build_match_prompt(resume_content, request.job_description)

    # 3. Call LLM and parse result (Service 3)
    llm = get_llm_service()
    result = await llm.match_resume(prompt)

    # 4. Map to API response schema
    return ResumeMatchResponse(
        code=200,
        status="ok",
        data=MatchResponseData(
            match_score=result.match_score,
            match_breakdown=MatchBreakdown(
                skills_match=result.match_breakdown.skills_match,
                experience_match=result.match_breakdown.experience_match,
                education_match=result.match_breakdown.education_match,
                keywords_match=result.match_breakdown.keywords_match
            ),
            suggestions=[
                MatchSuggestion(
                    category=s.category,
                    priority=s.priority,
                    title=s.title,
                    description=s.description,
                    action=s.action or "N/A"
                )
                for s in result.suggestions
            ]
        )
    )


@router.post("/optimize", response_model=ResumeOptimizeResponse)
async def optimize_resume(request: ResumeOptimizeRequest):
    """
    Optimize resume content using LLM.
    """
    # 1. Get resume content (Service 1)
    resume_content = await get_resume_content(request.session_id)

    # 2. Build optimize prompt (Service 2)
    builder = get_prompt_builder()
    prompt = builder.build_optimize_prompt(
        resume_content, 
        request.job_description, 
        request.template
    )

    # 3. Call LLM (Service 3)
    llm = get_llm_service()
    result = await llm.optimize_resume(prompt)

    # 4. Convert optimized markdown to PDF and HTML preview
    pdf_bytes = markdown_to_pdf(result.optimized_content)
    encoded_pdf = base64.b64encode(pdf_bytes).decode()
    optimized_html = markdown_to_html(result.optimized_content)

    return ResumeOptimizeResponse(
        code=200,
        status="ok",
        data=OptimizeResponseData(
            encoded_file=encoded_pdf,
            optimized_html=optimized_html,
        )
    )
