"""
Tests for Optimize Resume Endpoint (RA-45, RA-46, RA-47)

Updated for RA-82: /optimize now enqueues an async job and returns 202 + job_id
instead of blocking on LLM and returning the PDF directly.
"""

from unittest.mock import AsyncMock, MagicMock, patch

from app.core.config import settings


MOCK_RESUME_TEXT = """# John Doe
Email: john@example.com

## Experience
Software Engineer at Tech Corp (2020-2024)
- Built web applications
"""


@patch("app.api.routes.resumes.get_job_manager")
@patch("app.api.routes.resumes.get_resume_content", new_callable=AsyncMock)
def test_optimize_resume_without_jd(mock_get_content, mock_get_manager, client):
    """RA-45/RA-82: Test optimize without job description enqueues job and returns 202"""
    mock_get_content.return_value = MOCK_RESUME_TEXT

    mock_manager = MagicMock()
    mock_manager.enqueue.return_value = "test-job-id-123"
    mock_manager.queue_depth = 0
    mock_get_manager.return_value = mock_manager

    response = client.post(
        f"{settings.API_PREFIX}/resumes/optimize",
        json={"session_id": "test-session-123"},
    )

    assert response.status_code == 202
    data = response.json()

    assert data["code"] == 202
    assert data["status"] == "ok"
    assert data["data"]["job_id"] == "test-job-id-123"
    assert data["data"]["job_type"] == "optimize"
    assert data["data"]["status"] == "pending"


@patch("app.api.routes.resumes.get_job_manager")
@patch("app.api.routes.resumes.get_resume_content", new_callable=AsyncMock)
def test_optimize_resume_with_jd(mock_get_content, mock_get_manager, client):
    """RA-46/RA-82: Test optimize with job description enqueues job and returns 202"""
    mock_get_content.return_value = MOCK_RESUME_TEXT

    mock_manager = MagicMock()
    mock_manager.enqueue.return_value = "test-job-id-456"
    mock_manager.queue_depth = 1
    mock_get_manager.return_value = mock_manager

    response = client.post(
        f"{settings.API_PREFIX}/resumes/optimize",
        json={
            "session_id": "test-session-456",
            "job_description": "Senior Software Engineer position",
        },
    )

    assert response.status_code == 202
    data = response.json()

    assert data["code"] == 202
    assert data["status"] == "ok"
    assert data["data"]["job_id"] == "test-job-id-456"
    assert data["data"]["job_type"] == "optimize"
    assert data["data"]["queue_depth"] == 1


def test_optimize_resume_missing_session_id(client):
    """Test optimize endpoint requires session_id"""
    response = client.post(
        f"{settings.API_PREFIX}/resumes/optimize",
        json={},
    )

    assert response.status_code == 422


def test_prompt_builder_optimize_without_jd():
    """RA-45: Test prompt builder generates optimize prompt without JD"""
    from app.services.prompt.builder import get_prompt_builder

    builder = get_prompt_builder()
    prompt = builder.build_optimize_prompt("Some resume content")

    assert "Some resume content" in prompt
    assert "Target Job Description" not in prompt


def test_prompt_builder_optimize_with_jd():
    """RA-46: Test prompt builder generates optimize prompt with JD"""
    from app.services.prompt.builder import get_prompt_builder

    builder = get_prompt_builder()
    prompt = builder.build_optimize_prompt(
        "Some resume content", "Senior Engineer at Google"
    )

    assert "Some resume content" in prompt
    assert "Senior Engineer at Google" in prompt
    assert "Target Job Description" in prompt


def test_prompt_builder_optimize_empty_content():
    """Test prompt builder rejects empty resume content"""
    import pytest
    from app.services.prompt.builder import get_prompt_builder

    builder = get_prompt_builder()
    with pytest.raises(ValueError, match="resume_content cannot be empty"):
        builder.build_optimize_prompt("")
