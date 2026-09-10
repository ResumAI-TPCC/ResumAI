"""
Tests for mock interview start API.
"""

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import settings
from app.schemas.interview_schema import StartInterviewRequest
from app.services.interview_service import start_interview
from app.services.jobs.job_manager import QueueFullError
from app.services.llm.exceptions import LLMResponseError


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
      "question": "Please introduce yourself by connecting your FastAPI services experience to Tech Corp's need for a Python engineer with API experience.",
      "resume_evidence": "Built FastAPI services for analytics workflows",
      "jd_evidence": "Python engineer with API experience",
      "focus_areas": ["motivation", "role fit"]
    },
    {
      "id": "q2",
      "type": "resume_based",
      "label": "Resume-based",
      "question": "Which FastAPI service from your resume best demonstrates the API experience required in this Software Engineer JD?",
      "resume_evidence": "Built FastAPI services for analytics workflows",
      "jd_evidence": "API experience",
      "focus_areas": ["resume relevance", "ownership"]
    },
    {
      "id": "q3",
      "type": "project_followup",
      "label": "Project Follow-up",
      "question": "When you improved API latency by 30%, what trade-offs did you make that would matter for a Python API engineering role?",
      "resume_evidence": "Improved API latency by 30%",
      "jd_evidence": "Python engineer with API experience",
      "focus_areas": ["technical depth", "decision making"]
    },
    {
      "id": "q4",
      "type": "jd_skill_match",
      "label": "JD Skill Match",
      "question": "The JD requires Python and API experience. How have your Python, FastAPI, and GCP skills shown that readiness in practice?",
      "resume_evidence": "Skills: Python, FastAPI, React, GCP",
      "jd_evidence": "Python engineer with API experience",
      "focus_areas": ["skill alignment", "evidence"]
    },
    {
      "id": "q5",
      "type": "behavioral",
      "label": "Behavioral",
      "question": "Tell me about a time your backend engineering work on analytics workflows required collaboration while delivering reliable API results for a role needing API experience.",
      "resume_evidence": "FastAPI services for analytics workflows",
      "jd_evidence": "API experience",
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
    service.generate_text = AsyncMock(return_value=MockLLMResponse(content=content))
    return service


@patch("app.services.interview_service.get_llm_service")
@patch("app.services.interview_service.get_resume_content", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_start_interview_service_success(mock_get_content, mock_get_llm):
    mock_get_content.return_value = MOCK_RESUME_TEXT
    mock_get_llm.return_value = _mock_llm_service(MOCK_QUESTION_JSON)

    response = await start_interview(
        StartInterviewRequest(
            session_id="7c9e6679-7425-40de-944b-e07fc1f90ae7",
            job_description="We need a Python engineer with API experience.",
            job_title="Software Engineer",
            company_name="Tech Corp",
            question_count=5,
        )
    )

    assert response.code == 200
    assert response.status == "ok"
    assert response.data.interview_id.startswith("mock-")
    assert len(response.data.questions) == 5
    assert response.data.questions[0].id == "q1"
    assert response.data.questions[0].type == "self_intro"
    assert "FastAPI services" in response.data.questions[0].question
    assert response.data.questions[0].resume_evidence
    assert response.data.questions[0].jd_evidence
    assert mock_get_content.await_count == 1
    assert mock_get_llm.return_value.generate_text.await_count == 1
    messages = mock_get_llm.return_value.generate_text.await_args.args[0]
    assert len(messages) == 1
    assert "Candidate Resume" in messages[0].content


@patch("app.services.interview_service.get_interview_prompt_builder")
@patch("app.services.interview_service.get_llm_service")
@patch("app.services.interview_service.get_resume_content", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_start_interview_formats_prompt_once(
    mock_get_content,
    mock_get_llm,
    mock_get_builder,
):
    mock_get_content.return_value = MOCK_RESUME_TEXT
    mock_get_llm.return_value = _mock_llm_service(MOCK_QUESTION_JSON)
    builder = MagicMock()
    builder.build_question_generation_prompt.return_value = "question prompt"
    mock_get_builder.return_value = builder

    await start_interview(
        StartInterviewRequest(
            session_id="7c9e6679-7425-40de-944b-e07fc1f90ae7",
            job_description="We need a Python engineer with API experience.",
            question_count=5,
        )
    )

    builder.validate_question_generation_inputs.assert_called_once()
    builder.build_question_generation_prompt.assert_called_once()


@patch("app.api.routes.interviews.get_job_manager")
@patch(
    "app.api.routes.interviews.validate_start_interview_request",
    new_callable=AsyncMock,
)
def test_start_interview_enqueues_job(mock_validate, mock_get_manager, client):
    manager = MagicMock()
    manager.enqueue.return_value = "interview-job-123"
    manager.queue_depth = 1
    mock_get_manager.return_value = manager

    request_json = {
        "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "job_description": "We need a Python engineer with API experience.",
        "question_count": 5,
    }
    response = client.post(
        f"{settings.API_PREFIX}/interviews/start",
        json=request_json,
    )

    assert response.status_code == 202
    assert response.json()["data"] == {
        "job_id": "interview-job-123",
        "job_type": "interview_start",
        "status": "pending",
        "queue_depth": 1,
    }
    mock_validate.assert_awaited_once()
    manager.enqueue.assert_called_once()
    assert manager.enqueue.call_args.args[0] == "interview_start"


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
@pytest.mark.asyncio
async def test_start_interview_invalid_llm_json_fails_job_execution(
    mock_get_content,
    mock_get_llm,
):
    mock_get_content.return_value = MOCK_RESUME_TEXT
    mock_get_llm.return_value = _mock_llm_service("not json")

    request = StartInterviewRequest(
        session_id="7c9e6679-7425-40de-944b-e07fc1f90ae7",
        job_description="We need a Python engineer with API experience.",
        question_count=5,
    )
    with pytest.raises(LLMResponseError):
        await start_interview(request)


@patch("app.services.interview_service.get_llm_service")
@patch("app.services.interview_service.get_resume_content", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_start_interview_missing_evidence_fails_job_execution(
    mock_get_content,
    mock_get_llm,
):
    mock_get_content.return_value = MOCK_RESUME_TEXT
    mock_get_llm.return_value = _mock_llm_service(
        """
        {
          "questions": [
            {
              "id": "q1",
              "type": "self_intro",
              "label": "Self Introduction",
              "question": "Please introduce yourself.",
              "focus_areas": ["motivation"]
            },
            {
              "id": "q2",
              "type": "resume_based",
              "label": "Resume-based",
              "question": "Tell me about your resume.",
              "focus_areas": ["resume relevance"]
            },
            {
              "id": "q3",
              "type": "project_followup",
              "label": "Project Follow-up",
              "question": "Tell me about a project.",
              "focus_areas": ["technical depth"]
            },
            {
              "id": "q4",
              "type": "jd_skill_match",
              "label": "JD Skill Match",
              "question": "How do you match the JD?",
              "focus_areas": ["skill alignment"]
            },
            {
              "id": "q5",
              "type": "behavioral",
              "label": "Behavioral",
              "question": "Tell me about teamwork.",
              "focus_areas": ["collaboration"]
            }
          ]
        }
        """
    )

    request = StartInterviewRequest(
        session_id="7c9e6679-7425-40de-944b-e07fc1f90ae7",
        job_description="We need a Python engineer with API experience.",
        question_count=5,
    )
    with pytest.raises(LLMResponseError):
        await start_interview(request)


@patch("app.api.routes.interviews.get_job_manager")
@patch(
    "app.api.routes.interviews.validate_start_interview_request",
    new_callable=AsyncMock,
)
def test_start_interview_returns_429_when_queue_is_full(
    mock_validate,
    mock_get_manager,
    client,
):
    manager = MagicMock()
    manager.enqueue.side_effect = QueueFullError("full")
    mock_get_manager.return_value = manager

    response = client.post(
        f"{settings.API_PREFIX}/interviews/start",
        json={
            "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
            "job_description": "We need a Python engineer with API experience.",
            "question_count": 5,
        },
    )

    assert response.status_code == 429
    assert response.json()["detail"] == "Queue is full. Please retry later."
    mock_validate.assert_awaited_once()
