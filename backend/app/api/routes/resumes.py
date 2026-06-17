"""
Resume API Routes

Supports both synchronous and asynchronous (async queue) processing.
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
    JobCreateResponse,
    JobCreateData,
)
from fastapi import Request

from app.services.resume_service import get_resume_content, upload_resume_to_gcs
from app.services.pdf_service import markdown_to_pdf
from app.services.prompt.builder import get_prompt_builder
from app.services.llm.llm_service import get_llm_service
from app.services.llm.exceptions import (
    LLMServiceUnavailableError,
    LLMResponseError,
    LLMException,
)
from app.services.validators.content_moderator import ContentModerationError
from app.services.validators.content_moderator import get_content_moderator
from app.services.jobs.schemas import JobPayload
from app.services.jobs.manager import JobRunnerUnavailableError
from app.core.error_templates import (
    RESUME_EMPTY_CONTENT,
    CONTENT_MODERATION_INPUT_BLOCKED,
    CONTENT_MODERATION_OUTPUT_BLOCKED,
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


# ============================================================================
# Async Job Endpoints (New)
# ============================================================================

@router.post("/analyze/async", response_model=JobCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def analyze_resume_async(request: ResumeAnalyzeRequest, req: Request):
    """
    Analyze resume quality using LLM (async).

    Creates a background job and returns job_id for polling.
    Use GET /api/jobs/{job_id} to check status and retrieve result.
    """
    try:
        await get_resume_content(request.session_id)
    except HTTPException as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Resume not found") from e
        raise

    payload = JobPayload(
        task_type="analyze",
        session_id=request.session_id,
        arguments={"session_id": request.session_id},
    )
    try:
        receipt = req.app.state.job_manager.submit_job(payload)
    except JobRunnerUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    return JobCreateResponse(
        code=202,
        status="accepted",
        data=JobCreateData(job_id=receipt.job_id),
    )


@router.post("/match/async", response_model=JobCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def match_resume_async(request: ResumeMatchRequest, req: Request):
    """
    Match resume with job description using LLM (async).

    Creates a background job and returns job_id for polling.
    Use GET /api/jobs/{job_id} to check status and retrieve result.
    """
    try:
        await get_resume_content(request.session_id)
    except HTTPException as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Resume not found") from e
        raise

    payload = JobPayload(
        task_type="match",
        session_id=request.session_id,
        arguments={
            "session_id": request.session_id,
            "job_description": request.job_description,
            "job_title": request.job_title or "",
            "company_name": request.company_name or "",
        },
    )
    try:
        receipt = req.app.state.job_manager.submit_job(payload)
    except JobRunnerUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    return JobCreateResponse(
        code=202,
        status="accepted",
        data=JobCreateData(job_id=receipt.job_id),
    )


@router.post("/optimize/async", response_model=JobCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def optimize_resume_async(request: ResumeOptimizeRequest, req: Request):
    """
    Optimize resume content using LLM (async).

    Creates a background job and returns job_id for polling.
    Use GET /api/jobs/{job_id} to check status and retrieve result.
    """
    try:
        await get_resume_content(request.session_id)
    except HTTPException as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Resume not found") from e
        raise

    payload = JobPayload(
        task_type="optimize",
        session_id=request.session_id,
        arguments={
            "session_id": request.session_id,
            "job_description": request.job_description or "",
            "template": request.template,
        },
    )
    try:
        receipt = req.app.state.job_manager.submit_job(payload)
    except JobRunnerUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    return JobCreateResponse(
        code=202,
        status="accepted",
        data=JobCreateData(job_id=receipt.job_id),
    )


# ============================================================================
# Synchronous Endpoints (Existing - Kept for backward compatibility)
# ============================================================================

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

        # 1.5 Content moderation - check input (RA-62)
        moderator = get_content_moderator()
        is_safe, reason = moderator.check_input(resume_content)
        if not is_safe:
            raise HTTPException(
                status_code=CONTENT_MODERATION_INPUT_BLOCKED.code,
                detail=reason
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
    except ContentModerationError as e:
        raise HTTPException(
            status_code=CONTENT_MODERATION_OUTPUT_BLOCKED.code,
            detail=e.message
        ) from e
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

        has_job_description = bool(request.job_description and request.job_description.strip())
        has_job_title = bool(request.job_title and request.job_title.strip())
        has_company_name = bool(request.company_name and request.company_name.strip())

        # New match trigger logic:
        # Use match when any one of JD / Job Title / Company Name is present.
        if has_job_description:
            match_context = request.job_description.strip()
        elif has_job_title or has_company_name:
            match_context = (
                "Target role context:\n"
                f"Company: {(request.company_name or '').strip() or 'N/A'}\n"
                f"Job Title: {(request.job_title or '').strip() or 'N/A'}\n"
                "Use this context to evaluate resume-job fit."
            )
        else:
            raise ValueError(
                "Please provide at least one of Job Description, Job Title, or Company Name for matching."
            )

        # 1.5 Content moderation - check inputs (RA-62)
        moderator = get_content_moderator()
        is_safe, reason = moderator.check_input(resume_content)
        if not is_safe:
            raise HTTPException(
                status_code=CONTENT_MODERATION_INPUT_BLOCKED.code,
                detail=reason
            )
        is_safe, reason = moderator.check_input(match_context)
        if not is_safe:
            raise HTTPException(
                status_code=CONTENT_MODERATION_INPUT_BLOCKED.code,
                detail=reason
            )

        # 2. Build match prompt (Service 2)
        builder = get_prompt_builder()
        prompt = builder.build_match_prompt(resume_content, match_context)

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
    except ValueError as e:
        # JD quality validation errors from PromptBuilder
        raise HTTPException(
            status_code=400,
            detail=str(e)
        ) from e
    except ContentModerationError as e:
        raise HTTPException(
            status_code=CONTENT_MODERATION_OUTPUT_BLOCKED.code,
            detail=e.message
        ) from e
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

        # 1.5 Content moderation - check inputs (RA-62)
        moderator = get_content_moderator()
        is_safe, reason = moderator.check_input(resume_content)
        if not is_safe:
            raise HTTPException(
                status_code=CONTENT_MODERATION_INPUT_BLOCKED.code,
                detail=reason
            )
        if request.job_description:
            is_safe, reason = moderator.check_input(request.job_description)
            if not is_safe:
                raise HTTPException(
                    status_code=CONTENT_MODERATION_INPUT_BLOCKED.code,
                    detail=reason
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

        # 4. Convert optimized content to PDF and encode as base64
        import base64
        pdf_bytes = markdown_to_pdf(result.optimized_content)
        encoded_content = base64.b64encode(pdf_bytes).decode()

        return ResumeOptimizeResponse(
            code=200,
            status="ok",
            data=OptimizeResponseData(encoded_file=encoded_content)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except ContentModerationError as e:
        raise HTTPException(
            status_code=CONTENT_MODERATION_OUTPUT_BLOCKED.code,
            detail=e.message
        ) from e
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
