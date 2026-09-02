"""
Tests for mock interview answer evaluation API.
"""

import json
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import settings
from app.schemas.interview_schema import EvaluateAnswerRequest
from app.services.interview_service import evaluate_interview_answer
from app.services.llm.exceptions import LLMResponseError


MOCK_RESUME_TEXT = """Jane Doe
Backend Engineer

Experience:
- Built FastAPI services for analytics workflows.
- Improved API latency by 30%.

Skills: Python, FastAPI, React, GCP
"""


MOCK_FEEDBACK_JSON = """
{
  "question_id": "q2",
  "score": 82,
  "strengths": [
    "The answer uses a relevant FastAPI service example.",
    "The answer connects backend experience to the API-focused JD."
  ],
  "weaknesses": [
    "The answer could quantify the production impact more clearly.",
    "The structure can separate context, action, and result more explicitly."
  ],
  "suggestions": [
    "Add one metric such as latency, throughput, or user impact.",
    "Use a short STAR structure to make ownership and outcome easier to follow."
  ],
  "improved_answer": "A stronger answer would briefly describe the analytics workflow, clarify the FastAPI ownership, and end with the 30% latency improvement.",
  "jd_alignment": "Strong alignment with the JD's Python and API experience requirement because the answer references FastAPI backend work.",
  "scoring_breakdown": {
    "relevance": 24,
    "specificity": 20,
    "structure": 16,
    "impact": 12,
    "communication": 10
  }
}
"""


@dataclass
class MockLLMResponse:
    content: str
    model: str = "mock-model"
    usage: dict | None = None


def _mock_llm_service(content: str):
    service = MagicMock()
    service.generate_text = AsyncMock(return_value=MockLLMResponse(content=content))
    return service


def _answer_payload(answer: str = "I built FastAPI services for analytics workflows."):
    return {
        "interview_id": "mock-123",
        "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "question_id": "q2",
        "question_type": "resume_based",
        "question": "Which FastAPI service best proves your API experience?",
        "resume_evidence": "Built FastAPI services for analytics workflows",
        "jd_evidence": "Python engineer with API experience",
        "focus_areas": ["resume relevance", "ownership"],
        "answer": answer,
        "job_description": "We need a Python engineer with API experience.",
        "job_title": "Software Engineer",
        "company_name": "Tech Corp",
    }


@patch("app.services.interview_service.get_llm_service")
@patch("app.services.interview_service.get_resume_content", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_evaluate_interview_answer_service_success(
    mock_get_content,
    mock_get_llm,
):
    mock_get_content.return_value = MOCK_RESUME_TEXT
    mock_get_llm.return_value = _mock_llm_service(MOCK_FEEDBACK_JSON)

    response = await evaluate_interview_answer(
        EvaluateAnswerRequest(**_answer_payload())
    )

    assert response.code == 200
    assert response.status == "ok"
    assert response.data.question_id == "q2"
    assert response.data.score == 82
    assert len(response.data.strengths) == 2
    assert "FastAPI" in response.data.improved_answer
    assert response.data.scoring_breakdown.relevance == 24
    assert mock_get_content.await_count == 1
    assert mock_get_llm.return_value.generate_text.await_count == 1
    messages = mock_get_llm.return_value.generate_text.await_args.args[0]
    assert len(messages) == 1
    assert "Candidate Answer" in messages[0].content


@patch("app.services.interview_service.get_interview_prompt_builder")
@patch("app.services.interview_service.get_llm_service")
@patch("app.services.interview_service.get_resume_content", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_evaluate_interview_answer_formats_prompt_once(
    mock_get_content,
    mock_get_llm,
    mock_get_builder,
):
    mock_get_content.return_value = MOCK_RESUME_TEXT
    mock_get_llm.return_value = _mock_llm_service(MOCK_FEEDBACK_JSON)
    builder = MagicMock()
    builder.build_answer_evaluation_prompt.return_value = "answer prompt"
    mock_get_builder.return_value = builder

    await evaluate_interview_answer(EvaluateAnswerRequest(**_answer_payload()))

    builder.validate_answer_evaluation_inputs.assert_called_once()
    builder.build_answer_evaluation_prompt.assert_called_once()


@patch("app.api.routes.interviews.get_job_manager")
@patch(
    "app.api.routes.interviews.validate_interview_answer_request",
    new_callable=AsyncMock,
)
def test_evaluate_interview_answer_enqueues_job(
    mock_validate,
    mock_get_manager,
    client,
):
    manager = MagicMock()
    manager.enqueue.return_value = "answer-job-123"
    manager.queue_depth = 2
    mock_get_manager.return_value = manager

    response = client.post(
        f"{settings.API_PREFIX}/interviews/answer",
        json=_answer_payload(),
    )

    assert response.status_code == 202
    assert response.json()["data"] == {
        "job_id": "answer-job-123",
        "job_type": "interview_answer",
        "status": "pending",
        "queue_depth": 2,
    }
    mock_validate.assert_awaited_once()
    manager.enqueue.assert_called_once()
    assert manager.enqueue.call_args.args[0] == "interview_answer"


@patch("app.services.interview_service.get_llm_service")
@patch("app.services.interview_service.get_resume_content", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_evaluate_interview_answer_empty_feedback_lists_use_fallbacks(
    mock_get_content,
    mock_get_llm,
):
    mock_get_content.return_value = MOCK_RESUME_TEXT
    feedback = json.loads(MOCK_FEEDBACK_JSON)
    feedback["strengths"] = []
    feedback["weaknesses"] = []
    feedback["suggestions"] = []
    feedback["score"] = 5
    feedback["scoring_breakdown"] = {
        "relevance": 0,
        "specificity": 0,
        "structure": 0,
        "impact": 0,
        "communication": 5,
    }
    mock_get_llm.return_value = _mock_llm_service(json.dumps(feedback))

    response = await evaluate_interview_answer(
        EvaluateAnswerRequest(
            **_answer_payload(
                answer=(
                    "I enjoy watching movies on weekends and discussing them with "
                    "friends, but this does not address the interview question."
                )
            )
        )
    )

    assert response.data.score == 5
    assert response.data.strengths
    assert response.data.weaknesses
    assert response.data.suggestions


@patch("app.services.interview_service.get_resume_content", new_callable=AsyncMock)
def test_evaluate_interview_answer_rejects_empty_answer(mock_get_content, client):
    mock_get_content.return_value = MOCK_RESUME_TEXT

    response = client.post(
        f"{settings.API_PREFIX}/interviews/answer",
        json=_answer_payload(answer="   "),
    )

    assert response.status_code == 400
    assert "answer cannot be empty" in response.json()["detail"]


@patch("app.services.interview_service.get_llm_service")
@patch("app.services.interview_service.get_resume_content", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_evaluate_interview_answer_low_signal_answer_returns_feedback(
    mock_get_content,
    mock_get_llm,
):
    mock_get_content.return_value = MOCK_RESUME_TEXT

    response = await evaluate_interview_answer(
        EvaluateAnswerRequest(**_answer_payload(answer="123"))
    )

    assert response.data.question_id == "q2"
    assert response.data.score == 8
    assert response.data.weaknesses
    assert response.data.suggestions
    assert response.data.scoring_breakdown.specificity == 0
    mock_get_llm.assert_not_called()


@patch("app.services.interview_service.get_llm_service")
@patch("app.services.interview_service.get_resume_content", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_evaluate_interview_answer_invalid_json_fails_job_execution(
    mock_get_content,
    mock_get_llm,
):
    mock_get_content.return_value = MOCK_RESUME_TEXT
    mock_get_llm.return_value = _mock_llm_service("not json")

    with pytest.raises(LLMResponseError):
        await evaluate_interview_answer(EvaluateAnswerRequest(**_answer_payload()))


@patch("app.services.interview_service.get_llm_service")
@patch("app.services.interview_service.get_resume_content", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_evaluate_interview_answer_missing_feedback_fields_fails_job_execution(
    mock_get_content,
    mock_get_llm,
):
    mock_get_content.return_value = MOCK_RESUME_TEXT
    mock_get_llm.return_value = _mock_llm_service(
        """
        {
          "question_id": "q2",
          "score": 70,
          "strengths": ["Relevant example"]
        }
        """
    )

    with pytest.raises(LLMResponseError):
        await evaluate_interview_answer(EvaluateAnswerRequest(**_answer_payload()))
