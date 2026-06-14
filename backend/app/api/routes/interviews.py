"""
Mock Interview API Routes
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.error_templates import (
    CONTENT_MODERATION_OUTPUT_BLOCKED,
    INTERNAL_SERVER_ERROR,
    LLM_GENERIC_ERROR,
    LLM_INVALID_RESPONSE,
    LLM_SERVICE_UNAVAILABLE,
)
from app.schemas.interview_schema import (
    StartInterviewRequest,
    StartInterviewResponse,
)
from app.services.interview_service import start_interview
from app.services.llm.exceptions import (
    LLMException,
    LLMResponseError,
    LLMServiceUnavailableError,
)
from app.services.validators.content_moderator import ContentModerationError

router = APIRouter()


@router.post("/start", response_model=StartInterviewResponse)
async def start_mock_interview(request: StartInterviewRequest):
    """
    Generate tailored mock interview questions from uploaded resume and JD.
    """
    try:
        return await start_interview(request)
    except HTTPException:
        raise
    except ContentModerationError as exc:
        raise HTTPException(
            status_code=CONTENT_MODERATION_OUTPUT_BLOCKED.code,
            detail=exc.message,
        ) from exc
    except LLMServiceUnavailableError as exc:
        raise HTTPException(
            status_code=LLM_SERVICE_UNAVAILABLE.code,
            detail=LLM_SERVICE_UNAVAILABLE.detail,
        ) from exc
    except LLMResponseError as exc:
        raise HTTPException(
            status_code=LLM_INVALID_RESPONSE.code,
            detail=LLM_INVALID_RESPONSE.detail,
        ) from exc
    except LLMException as exc:
        raise HTTPException(
            status_code=LLM_GENERIC_ERROR.code,
            detail=LLM_GENERIC_ERROR.detail,
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=INTERNAL_SERVER_ERROR.code,
            detail=INTERNAL_SERVER_ERROR.detail,
        ) from exc
