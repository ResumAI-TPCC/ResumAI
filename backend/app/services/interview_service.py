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
from langchain_core.messages import HumanMessage

from app.core.error_templates import (
    CONTENT_MODERATION_INPUT_BLOCKED,
    RESUME_EMPTY_CONTENT,
)
from app.schemas.interview_schema import (
    EvaluateAnswerData,
    EvaluateAnswerRequest,
    EvaluateAnswerResponse,
    InterviewQuestion,
    ScoringBreakdown,
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

BREAKDOWN_LIMITS = {
    "relevance": 30,
    "specificity": 25,
    "structure": 20,
    "impact": 15,
    "communication": 10,
}


async def start_interview(
    request: StartInterviewRequest,
) -> StartInterviewResponse:
    """
    Generate a five-question mock interview set from resume content and JD.
    """
    resume_content = await validate_start_interview_request(request)

    builder = get_interview_prompt_builder()
    prompt = builder.build_question_generation_prompt(
        resume_content=resume_content,
        job_description=request.job_description,
        job_title=request.job_title,
        company_name=request.company_name,
        question_count=request.question_count,
    )

    llm = get_llm_service()
    response = await llm.generate_text([HumanMessage(content=prompt)])

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


async def validate_start_interview_request(
    request: StartInterviewRequest,
) -> str:
    """Validate cheap request concerns before an interview job is enqueued."""
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

    try:
        get_interview_prompt_builder().validate_question_generation_inputs(
            resume_content=resume_content,
            job_description=request.job_description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return resume_content


async def evaluate_interview_answer(
    request: EvaluateAnswerRequest,
) -> EvaluateAnswerResponse:
    """
    Evaluate one mock interview answer with LLM-generated coaching feedback.
    """
    resume_content = await validate_interview_answer_request(request)

    if _is_low_signal_answer(request.answer):
        return EvaluateAnswerResponse(
            code=200,
            status="ok",
            data=_build_low_signal_feedback(request.question_id),
        )

    builder = get_interview_prompt_builder()
    prompt = builder.build_answer_evaluation_prompt(
        resume_content=resume_content,
        job_description=request.job_description,
        job_title=request.job_title,
        company_name=request.company_name,
        question_id=request.question_id,
        question_type=request.question_type,
        question=request.question,
        resume_evidence=request.resume_evidence,
        jd_evidence=request.jd_evidence,
        focus_areas=request.focus_areas,
        answer=request.answer,
    )

    llm = get_llm_service()
    response = await llm.generate_text([HumanMessage(content=prompt)])

    moderator = get_content_moderator()
    is_safe, reason = moderator.check_output(response.content)
    if not is_safe:
        raise ContentModerationError(reason)

    feedback = _parse_answer_feedback(
        content=response.content,
        question_id=request.question_id,
    )

    return EvaluateAnswerResponse(
        code=200,
        status="ok",
        data=feedback,
    )


async def validate_interview_answer_request(
    request: EvaluateAnswerRequest,
) -> str:
    """Validate cheap request concerns before an answer job is enqueued."""
    resume_content = await get_resume_content(request.session_id)
    if not resume_content or not resume_content.strip():
        raise HTTPException(
            status_code=RESUME_EMPTY_CONTENT.code,
            detail=RESUME_EMPTY_CONTENT.detail,
        )
    if not request.answer or not request.answer.strip():
        raise HTTPException(status_code=400, detail="answer cannot be empty")

    _moderate_answer_inputs(
        resume_content=resume_content,
        job_description=request.job_description,
        question=request.question,
        answer=request.answer,
        job_title=request.job_title,
        company_name=request.company_name,
        resume_evidence=request.resume_evidence,
        jd_evidence=request.jd_evidence,
        focus_areas=request.focus_areas,
    )

    if not _is_low_signal_answer(request.answer):
        try:
            get_interview_prompt_builder().validate_answer_evaluation_inputs(
                resume_content=resume_content,
                job_description=request.job_description,
                question=request.question,
                answer=request.answer,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    return resume_content


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
        _check_moderation_value(value, moderator)


def _moderate_answer_inputs(
    resume_content: str,
    job_description: str,
    question: str,
    answer: str,
    job_title: str | None,
    company_name: str | None,
    resume_evidence: str | None,
    jd_evidence: str | None,
    focus_areas: list[str],
) -> None:
    """Run content moderation against answer-evaluation inputs."""
    moderator = get_content_moderator()
    for value in [
        resume_content,
        job_description,
        question,
        answer,
        job_title or "",
        company_name or "",
        resume_evidence or "",
        jd_evidence or "",
        " ".join(focus_areas),
    ]:
        _check_moderation_value(value, moderator)


def _check_moderation_value(value: str, moderator: Any) -> None:
    """Raise a request error when an input moderation check fails."""
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
        question_text = str(item.get("question") or item.get("prompt") or "").strip()
        if not question_text:
            raise LLMResponseError("Interview question text cannot be empty")

        resume_evidence = str(
            item.get("resume_evidence") or item.get("resumeEvidence") or ""
        ).strip()
        jd_evidence = str(
            item.get("jd_evidence") or item.get("jdEvidence") or ""
        ).strip()
        if not resume_evidence or not jd_evidence:
            raise LLMResponseError(
                "Interview question response must include resume_evidence "
                "and jd_evidence for every question"
            )

        focus_areas = item.get("focus_areas") or item.get("focusAreas") or []
        if not isinstance(focus_areas, list):
            focus_areas = []
        normalized_focus_areas = [
            str(area).strip() for area in focus_areas if str(area).strip()
        ][:4]

        questions.append(
            InterviewQuestion(
                id=f"q{index + 1}",
                type=expected_type,
                label=expected_label,
                question=question_text,
                resume_evidence=resume_evidence,
                jd_evidence=jd_evidence,
                focus_areas=normalized_focus_areas
                or DEFAULT_FOCUS_AREAS[expected_type],
            )
        )

    return questions


def _is_low_signal_answer(answer: str) -> bool:
    """Detect answers that are too short or non-semantic to send to the LLM."""
    normalized = answer.strip()
    if len(normalized) < 8:
        return True

    has_language_character = re.search(r"[A-Za-z\u4e00-\u9fff]", normalized)
    if not has_language_character:
        return True

    word_count = len(normalized.split())
    if word_count <= 2 and len(normalized) < 20:
        return True

    return False


def _build_low_signal_feedback(question_id: str) -> EvaluateAnswerData:
    """Return deterministic coaching when an answer has too little signal."""
    return EvaluateAnswerData(
        question_id=question_id,
        score=8,
        strengths=[
            "You submitted a response, so this can be improved into a structured answer.",
        ],
        weaknesses=[
            "The answer is too short to evaluate against the interview question.",
            "It does not provide a concrete example, resume evidence, or JD alignment.",
        ],
        suggestions=[
            "Answer in 4-6 sentences using context, your action, and the result.",
            "Mention one concrete resume detail and connect it to one JD requirement.",
            "Add a metric, technical detail, or outcome so the interviewer can judge impact.",
        ],
        improved_answer=(
            "A stronger answer should briefly name the relevant experience, explain "
            "your specific contribution, connect it to the role requirement, and end "
            "with a concrete result or lesson learned."
        ),
        jd_alignment=(
            "This answer does not yet show alignment with the JD because it does not "
            "describe relevant skills, responsibilities, or evidence from the resume."
        ),
        scoring_breakdown=ScoringBreakdown(
            relevance=2,
            specificity=0,
            structure=2,
            impact=0,
            communication=4,
        ),
    )


def _normalize_text_list(
    value: Any,
    field_name: str,
    min_items: int = 1,
    max_items: int = 4,
    empty_fallback: str | None = None,
) -> list[str]:
    """Normalize and validate a short list of feedback text items."""
    if not isinstance(value, list):
        raise LLMResponseError(f"Interview feedback field {field_name} must be a list")

    items = [
        str(item).strip() for item in value if item is not None and str(item).strip()
    ][:max_items]
    if len(items) < min_items:
        if not items and empty_fallback:
            logger.warning(
                "Interview feedback field %s was empty; using fallback",
                field_name,
            )
            return [empty_fallback]
        raise LLMResponseError(f"Interview feedback field {field_name} cannot be empty")

    return items


def _parse_score(value: Any, field_name: str, min_value: int, max_value: int) -> int:
    """Parse and validate an integer score."""
    try:
        score = int(round(float(value)))
    except (TypeError, ValueError) as exc:
        raise LLMResponseError(
            f"Interview feedback field {field_name} is invalid"
        ) from exc

    if score < min_value or score > max_value:
        raise LLMResponseError(
            f"Interview feedback field {field_name} must be between "
            f"{min_value} and {max_value}"
        )

    return score


def _parse_scoring_breakdown(value: Any) -> ScoringBreakdown:
    """Parse and validate answer evaluation scoring breakdown."""
    if not isinstance(value, dict):
        raise LLMResponseError("Interview feedback scoring_breakdown must be an object")

    parsed = {
        field: _parse_score(value.get(field), field, 0, limit)
        for field, limit in BREAKDOWN_LIMITS.items()
    }
    return ScoringBreakdown(**parsed)


def _parse_answer_feedback(content: str, question_id: str) -> EvaluateAnswerData:
    """Parse and normalize the LLM answer-evaluation feedback."""
    data = _extract_json(content)
    if not data:
        raise LLMResponseError("Interview feedback response did not contain valid JSON")

    if isinstance(data.get("data"), dict):
        data = data["data"]
    elif isinstance(data.get("feedback"), dict):
        data = data["feedback"]

    breakdown = _parse_scoring_breakdown(
        data.get("scoring_breakdown")
        or data.get("scoringBreakdown")
        or data.get("breakdown")
    )
    breakdown_total = sum(getattr(breakdown, field) for field in BREAKDOWN_LIMITS)

    score = _parse_score(data.get("score"), "score", 0, 100)
    if abs(score - breakdown_total) > 10:
        logger.warning(
            "Interview feedback score adjusted from %s to breakdown total %s",
            score,
            breakdown_total,
        )
        score = breakdown_total

    improved_answer = str(
        data.get("improved_answer") or data.get("improvedAnswer") or ""
    ).strip()
    jd_alignment = str(
        data.get("jd_alignment") or data.get("jdAlignment") or ""
    ).strip()
    if not improved_answer:
        raise LLMResponseError("Interview feedback improved_answer cannot be empty")
    if not jd_alignment:
        raise LLMResponseError("Interview feedback jd_alignment cannot be empty")

    return EvaluateAnswerData(
        question_id=question_id,
        score=score,
        strengths=_normalize_text_list(
            data.get("strengths"),
            "strengths",
            empty_fallback=(
                "The response provides an attempt that can be redirected toward "
                "the interview question."
            ),
        ),
        weaknesses=_normalize_text_list(
            (
                data.get("weaknesses")
                if "weaknesses" in data
                else data.get("areas_for_improvement")
            ),
            "weaknesses",
            empty_fallback=(
                "The response does not yet provide enough relevant evidence to "
                "demonstrate role alignment."
            ),
        ),
        suggestions=_normalize_text_list(
            data.get("suggestions"),
            "suggestions",
            empty_fallback=(
                "Use one relevant resume example and connect it directly to the "
                "question and JD requirement."
            ),
        ),
        improved_answer=improved_answer,
        jd_alignment=jd_alignment,
        scoring_breakdown=breakdown,
    )
