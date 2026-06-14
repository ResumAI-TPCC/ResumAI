"""
Tests for mock interview start API.
"""

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


MOCK_QUESTION_JSON = """
{
  "questions": [
    {
      "id": "q1",
      "type": "self_intro",
      "label": "Self Introduction",
      "question": "Please introduce yourself and connect your backend experience to this role.",
      "focus_areas": ["motivation", "role fit"]
    },
    {
      "id": "q2",
      "type": "resume_based",
      "label": "Resume-based",
      "question": "Which FastAPI project from your resume best demonstrates your backend ability?",
      "focus_areas": ["resume relevance", "ownership"]
    },
    {
      "id": "q3",
      "type": "project_followup",
      "label": "Project Follow-up",
      "question": "What trade-offs did you make when improving API latency by 30%?",
      "focus_areas": ["technical depth", "decision making"]
    },
    {
      "id": "q4",
      "type": "jd_skill_match",
      "label": "JD Skill Match",
      "question": "The JD requires Python and API integration. How have you used those skills?",
      "focus_areas": ["skill alignment", "evidence"]
    },
    {
      "id": "q5",
      "type": "behavioral",
      "label": "Behavioral",
      "question": "Tell me about a time you solved a difficult engineering problem with teammates.",
      "focus_areas": ["collaboration", "reflection"]
    }
  ]
}
"""


@dataclass
class MockLLMResponse:
    content: str
    model: str = "mock-model"
    usage: dict | None = None


def _mock_llm_service(content: str):
    service = MagicMock()
    service.provider.analyze = AsyncMock(
        return_value=MockLLMResponse(content=content)
    )
    return service


@patch("app.services.interview_service.get_llm_service")
@patch("app.services.interview_service.get_resume_content", new_callable=AsyncMock)
def test_start_interview_success(mock_get_content, mock_get_llm, client):
    mock_get_content.return_value = MOCK_RESUME_TEXT
    mock_get_llm.return_value = _mock_llm_service(MOCK_QUESTION_JSON)

    response = client.post(
        f"{settings.API_PREFIX}/interviews/start",
        json={
            "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
            "job_description": "We need a Python engineer with API experience.",
            "job_title": "Software Engineer",
            "company_name": "Tech Corp",
            "question_count": 5,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 200
    assert payload["status"] == "ok"
    assert payload["data"]["interview_id"].startswith("mock-")
    assert len(payload["data"]["questions"]) == 5
    assert payload["data"]["questions"][0]["id"] == "q1"
    assert payload["data"]["questions"][0]["type"] == "self_intro"
    assert "backend experience" in payload["data"]["questions"][0]["question"]
    assert mock_get_content.await_count == 1
    assert mock_get_llm.return_value.provider.analyze.await_count == 1


@patch("app.services.interview_service.get_resume_content", new_callable=AsyncMock)
def test_start_interview_rejects_empty_jd(mock_get_content, client):
    mock_get_content.return_value = MOCK_RESUME_TEXT

    response = client.post(
        f"{settings.API_PREFIX}/interviews/start",
        json={
            "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
            "job_description": "   ",
            "question_count": 5,
        },
    )

    assert response.status_code == 400
    assert "job_description cannot be empty" in response.json()["detail"]


@patch("app.services.interview_service.get_llm_service")
@patch("app.services.interview_service.get_resume_content", new_callable=AsyncMock)
def test_start_interview_invalid_llm_json_returns_502(
    mock_get_content,
    mock_get_llm,
    client,
):
    mock_get_content.return_value = MOCK_RESUME_TEXT
    mock_get_llm.return_value = _mock_llm_service("not json")

    response = client.post(
        f"{settings.API_PREFIX}/interviews/start",
        json={
            "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
            "job_description": "We need a Python engineer with API experience.",
            "question_count": 5,
        },
    )

    assert response.status_code == 502
    assert "invalid response" in response.json()["detail"].lower()
