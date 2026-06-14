"""
Interview Service

Generates tailored mock interview questions from an uploaded resume and JD.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any

from fastapi import HTTPException

from app.core.error_templates import (
    CONTENT_MODERATION_INPUT_BLOCKED,
    RESUME_EMPTY_CONTENT,
)
from app.schemas.interview_schema import (
    InterviewQuestion,
    StartInterviewData,
    StartInterviewRequest,
    StartInterviewResponse,
)
from app.services.llm.exceptions import LLMResponseError
from app.services.llm.llm_service import get_llm_service
from app.services.prompt.interview_builder import get_interview_prompt_builder
from app.services.resume_service import get_resume_content
from app.services.validators.content_moderator import (
    ContentModerationError,
    get_content_moderator,
)

logger = logging.getLogger(__name__)

QUESTION_TYPES = [
    ("self_intro", "Self Introduction"),
    ("resume_based", "Resume-based"),
    ("project_followup", "Project Follow-up"),
    ("jd_skill_match", "JD Skill Match"),
    ("behavioral", "Behavioral"),
]

DEFAULT_FOCUS_AREAS = {
    "self_intro": ["motivation", "role fit", "career narrative"],
    "resume_based": ["resume relevance", "ownership", "impact"],
    "project_followup": ["technical depth", "decision making", "execution"],
    "jd_skill_match": ["skill alignment", "job readiness", "evidence"],
    "behavioral": ["collaboration", "problem solving", "reflection"],
}


async def start_interview(
    request: StartInterviewRequest,
) -> StartInterviewResponse:
    """
    Generate a five-question mock interview set from resume content and JD.
    """
    resume_content = await get_resume_content(request.session_id)
    if not resume_content or not resume_content.strip():
        raise HTTPException(
            status_code=RESUME_EMPTY_CONTENT.code,
            detail=RESUME_EMPTY_CONTENT.detail,
        )

    _moderate_inputs(
        resume_content=resume_content,
        job_description=request.job_description,
        job_title=request.job_title,
        company_name=request.company_name,
    )

    builder = get_interview_prompt_builder()
    try:
        prompt = builder.build_question_generation_prompt(
            resume_content=resume_content,
            job_description=request.job_description,
            job_title=request.job_title,
            company_name=request.company_name,
            question_count=request.question_count,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    llm = get_llm_service()
    response = await llm.provider.analyze(prompt, "")

    moderator = get_content_moderator()
    is_safe, reason = moderator.check_output(response.content)
    if not is_safe:
        raise ContentModerationError(reason)

    questions = _parse_questions(response.content, request.question_count)

    return StartInterviewResponse(
        code=200,
        status="ok",
        data=StartInterviewData(
            interview_id=f"mock-{uuid.uuid4()}",
            questions=questions,
        ),
    )


def _moderate_inputs(
    resume_content: str,
    job_description: str,
    job_title: str | None,
    company_name: str | None,
) -> None:
    """Run existing content moderation against all user-provided inputs."""
    moderator = get_content_moderator()
    for value in [
        resume_content,
        job_description,
        job_title or "",
        company_name or "",
    ]:
        is_safe, reason = moderator.check_input(value)
        if not is_safe:
            raise HTTPException(
                status_code=CONTENT_MODERATION_INPUT_BLOCKED.code,
                detail=reason,
            )


def _extract_json(content: str) -> dict[str, Any] | None:
    """Extract a JSON object from an LLM response."""
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
    if json_match:
        try:
            parsed = json.loads(json_match.group(1))
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            logger.warning("Failed to parse interview JSON markdown block")

    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", content)
    if match:
        try:
            parsed = json.loads(match.group())
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            logger.warning("Failed to parse extracted interview JSON object")

    return None


def _parse_questions(content: str, expected_count: int) -> list[InterviewQuestion]:
    """Parse and normalize the LLM question list."""
    data = _extract_json(content)
    if not data:
        raise LLMResponseError("Interview question response did not contain valid JSON")

    raw_questions = data.get("questions", [])
    if not isinstance(raw_questions, list) or len(raw_questions) < expected_count:
        raise LLMResponseError(
            f"Interview response must contain at least {expected_count} questions"
        )

    questions: list[InterviewQuestion] = []
    for index, item in enumerate(raw_questions[:expected_count]):
        if not isinstance(item, dict):
            raise LLMResponseError("Interview question item must be an object")

        expected_type, expected_label = QUESTION_TYPES[index]
        question_text = str(
            item.get("question") or item.get("prompt") or ""
        ).strip()
        if not question_text:
            raise LLMResponseError("Interview question text cannot be empty")

        focus_areas = item.get("focus_areas") or item.get("focusAreas") or []
        if not isinstance(focus_areas, list):
            focus_areas = []
        normalized_focus_areas = [
            str(area).strip()
            for area in focus_areas
            if str(area).strip()
        ][:4]

        questions.append(
            InterviewQuestion(
                id=f"q{index + 1}",
                type=expected_type,
                label=expected_label,
                question=question_text,
                focus_areas=normalized_focus_areas
                or DEFAULT_FOCUS_AREAS[expected_type],
            )
        )

    return questions
