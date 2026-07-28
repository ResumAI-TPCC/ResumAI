"""
Tests for mock interview answer evaluation API.
"""

import json
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.config import settings


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
def test_evaluate_interview_answer_success(mock_get_content, mock_get_llm, client):
    mock_get_content.return_value = MOCK_RESUME_TEXT
    mock_get_llm.return_value = _mock_llm_service(MOCK_FEEDBACK_JSON)

    response = client.post(
        f"{settings.API_PREFIX}/interviews/answer",
        json=_answer_payload(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 200
    assert payload["status"] == "ok"
    assert payload["data"]["question_id"] == "q2"
    assert payload["data"]["score"] == 82
    assert len(payload["data"]["strengths"]) == 2
    assert "FastAPI" in payload["data"]["improved_answer"]
    assert payload["data"]["scoring_breakdown"]["relevance"] == 24
    assert mock_get_content.await_count == 1
    assert mock_get_llm.return_value.generate_text.await_count == 1
    messages = mock_get_llm.return_value.generate_text.await_args.args[0]
    assert len(messages) == 1
    assert "Candidate Answer" in messages[0].content


@patch("app.services.interview_service.get_llm_service")
@patch("app.services.interview_service.get_resume_content", new_callable=AsyncMock)
def test_evaluate_interview_answer_empty_feedback_lists_use_fallbacks(
    mock_get_content,
    mock_get_llm,
    client,
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

    response = client.post(
        f"{settings.API_PREFIX}/interviews/answer",
        json=_answer_payload(
            answer=(
                "I enjoy watching movies on weekends and discussing them with "
                "friends, but this does not address the interview question."
            )
        ),
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["score"] == 5
    assert payload["strengths"]
    assert payload["weaknesses"]
    assert payload["suggestions"]


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
def test_evaluate_interview_answer_low_signal_answer_returns_feedback(
    mock_get_content,
    mock_get_llm,
    client,
):
    mock_get_content.return_value = MOCK_RESUME_TEXT

    response = client.post(
        f"{settings.API_PREFIX}/interviews/answer",
        json=_answer_payload(answer="123"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["question_id"] == "q2"
    assert payload["data"]["score"] == 8
    assert payload["data"]["weaknesses"]
    assert payload["data"]["suggestions"]
    assert payload["data"]["scoring_breakdown"]["specificity"] == 0
    mock_get_llm.assert_not_called()


@patch("app.services.interview_service.get_llm_service")
@patch("app.services.interview_service.get_resume_content", new_callable=AsyncMock)
def test_evaluate_interview_answer_invalid_json_returns_502(
    mock_get_content,
    mock_get_llm,
    client,
):
    mock_get_content.return_value = MOCK_RESUME_TEXT
    mock_get_llm.return_value = _mock_llm_service("not json")

    response = client.post(
        f"{settings.API_PREFIX}/interviews/answer",
        json=_answer_payload(),
    )

    assert response.status_code == 502
    assert "invalid response" in response.json()["detail"].lower()


@patch("app.services.interview_service.get_llm_service")
@patch("app.services.interview_service.get_resume_content", new_callable=AsyncMock)
def test_evaluate_interview_answer_missing_feedback_fields_returns_502(
    mock_get_content,
    mock_get_llm,
    client,
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

    response = client.post(
        f"{settings.API_PREFIX}/interviews/answer",
        json=_answer_payload(),
    )

    assert response.status_code == 502
    assert "invalid response" in response.json()["detail"].lower()
