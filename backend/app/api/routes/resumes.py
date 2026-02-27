"""
Resume API Routes
"""

from __future__ import annotations

from fastapi import APIRouter, File, UploadFile, HTTPException, status

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
from app.services.file_service import generate_and_encode_resume
from app.services.prompt.builder import get_prompt_builder
from app.services.llm.llm_service import get_llm_service
from app.services.llm.exceptions import (
    LLMServiceUnavailableError,
    LLMResponseError,
    LLMException,
)
from app.core.error_templates import (
    RESUME_EMPTY_CONTENT,
    LLM_SERVICE_UNAVAILABLE,
    LLM_INVALID_RESPONSE,
    LLM_GENERIC_ERROR,
    INTERNAL_SERVER_ERROR,
)

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
    try:
        # 1. Get resume text content (Service 1)
        resume_content = await get_resume_content(request.session_id)
        
        # Validate content is not empty
        if not resume_content or not resume_content.strip():
            raise HTTPException(
                status_code=RESUME_EMPTY_CONTENT.code,
                detail=RESUME_EMPTY_CONTENT.detail
            )

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
        
    except HTTPException:
        # Re-raise HTTP exceptions (from resume service, validation, etc.)
        raise
    except LLMServiceUnavailableError as e:
        raise HTTPException(
            status_code=LLM_SERVICE_UNAVAILABLE.code,
            detail=LLM_SERVICE_UNAVAILABLE.detail
        ) from e
    except LLMResponseError as e:
        raise HTTPException(
            status_code=LLM_INVALID_RESPONSE.code,
            detail=LLM_INVALID_RESPONSE.detail
        ) from e
    except LLMException as e:
        raise HTTPException(
            status_code=LLM_GENERIC_ERROR.code,
            detail=LLM_GENERIC_ERROR.detail
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=INTERNAL_SERVER_ERROR.code,
            detail=INTERNAL_SERVER_ERROR.detail
        ) from e


@router.post("/match", response_model=ResumeMatchResponse)
async def match_resume(request: ResumeMatchRequest):
    """
    Match resume with job description using LLM.
    """
    try:
        # 1. Get resume content (Service 1)
        resume_content = await get_resume_content(request.session_id)
        
        # Validate content is not empty
        if not resume_content or not resume_content.strip():
            raise HTTPException(
                status_code=RESUME_EMPTY_CONTENT.code,
                detail=RESUME_EMPTY_CONTENT.detail
            )

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
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except LLMServiceUnavailableError as e:
        raise HTTPException(
            status_code=LLM_SERVICE_UNAVAILABLE.code,
            detail=LLM_SERVICE_UNAVAILABLE.detail
        ) from e
    except LLMResponseError as e:
        raise HTTPException(
            status_code=LLM_INVALID_RESPONSE.code,
            detail=LLM_INVALID_RESPONSE.detail
        ) from e
    except LLMException as e:
        raise HTTPException(
            status_code=LLM_GENERIC_ERROR.code,
            detail=LLM_GENERIC_ERROR.detail
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=INTERNAL_SERVER_ERROR.code,
            detail=INTERNAL_SERVER_ERROR.detail
        ) from e


@router.post("/optimize", response_model=ResumeOptimizeResponse)
async def optimize_resume(request: ResumeOptimizeRequest):
    """
    Optimize resume content using LLM.
    """
    try:
        # 1. Get resume content (Service 1)
        resume_content = await get_resume_content(request.session_id)
        
        # Validate content is not empty
        if not resume_content or not resume_content.strip():
            raise HTTPException(
                status_code=RESUME_EMPTY_CONTENT.code,
                detail=RESUME_EMPTY_CONTENT.detail
            )

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

        # 4. Generate and encode file for download
        # Note: Using markdown format for MVP. PDF generation is available
        # in app.services.pdf_service and reserved for future use.
        encoded_content = generate_and_encode_resume(result.optimized_content)

        return ResumeOptimizeResponse(
            code=200,
            status="ok",
            data=OptimizeResponseData(encoded_file=encoded_content)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except LLMServiceUnavailableError as e:
        raise HTTPException(
            status_code=LLM_SERVICE_UNAVAILABLE.code,
            detail=LLM_SERVICE_UNAVAILABLE.detail
        ) from e
    except LLMResponseError as e:
        raise HTTPException(
            status_code=LLM_INVALID_RESPONSE.code,
            detail=LLM_INVALID_RESPONSE.detail
        ) from e
    except LLMException as e:
        raise HTTPException(
            status_code=LLM_GENERIC_ERROR.code,
            detail=LLM_GENERIC_ERROR.detail
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=INTERNAL_SERVER_ERROR.code,
            detail=INTERNAL_SERVER_ERROR.detail
        ) from e
