"""
Tests for Optimize Resume Endpoint (RA-45, RA-46, RA-47)
"""

import base64
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass

from app.core.config import settings


MOCK_RESUME_TEXT = """# John Doe
Email: john@example.com

## Experience
Software Engineer at Tech Corp (2020-2024)
- Built web applications
"""

MOCK_OPTIMIZED_WITHOUT_JD = """# John Doe
**Email:** john@example.com

## Professional Summary
Experienced software engineer with 4+ years of expertise.

## Work Experience
### Software Engineer | Tech Corp | 2020-2024
- Architected and developed 5 production web applications
- Optimized without JD
"""

MOCK_OPTIMIZED_WITH_JD = """# John Doe
**Email:** john@example.com

## Professional Summary
Results-driven software engineer aligned with Senior Engineer requirements.

## Work Experience
### Software Engineer | Tech Corp | 2020-2024
- Led development of microservices architecture
- Optimized with JD
"""


@dataclass
class MockOptimizeResult:
    optimized_content: str = ""


@patch("app.api.routes.resumes.get_llm_service")
@patch("app.api.routes.resumes.get_resume_content", new_callable=AsyncMock)
def test_optimize_resume_without_jd(mock_get_content, mock_get_llm, client):
    """RA-45: Test optimize without job description"""
    mock_get_content.return_value = MOCK_RESUME_TEXT

    mock_service = MagicMock()
    mock_service.optimize_resume = AsyncMock(
        return_value=MockOptimizeResult(optimized_content=MOCK_OPTIMIZED_WITHOUT_JD)
    )
    mock_get_llm.return_value = mock_service

    response = client.post(
        f"{settings.API_PREFIX}/resumes/optimize",
        json={"session_id": "test-session-123"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["code"] == 200
    assert data["status"] == "ok"
    assert "encoded_file" in data["data"]

    # Verify base64 decoding produces valid PDF
    decoded = base64.b64decode(data["data"]["encoded_file"])
    assert decoded[:5] == b"%PDF-", "Response should be a valid PDF file"


@patch("app.api.routes.resumes.get_llm_service")
@patch("app.api.routes.resumes.get_resume_content", new_callable=AsyncMock)
def test_optimize_resume_with_jd(mock_get_content, mock_get_llm, client):
    """RA-46: Test optimize with job description"""
    mock_get_content.return_value = MOCK_RESUME_TEXT

    mock_service = MagicMock()
    mock_service.optimize_resume = AsyncMock(
        return_value=MockOptimizeResult(optimized_content=MOCK_OPTIMIZED_WITH_JD)
    )
    mock_get_llm.return_value = mock_service

    response = client.post(
        f"{settings.API_PREFIX}/resumes/optimize",
        json={
            "session_id": "test-session-456",
            "job_description": "Senior Software Engineer position",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert "encoded_file" in data["data"]

    # Verify response is a valid PDF
    decoded = base64.b64decode(data["data"]["encoded_file"])
    assert decoded[:5] == b"%PDF-", "Response should be a valid PDF file"


def test_optimize_resume_missing_session_id(client):
    """Test optimize endpoint requires session_id"""
    response = client.post(
        f"{settings.API_PREFIX}/resumes/optimize",
        json={},
    )

    assert response.status_code == 422


def test_optimize_no_jd_prompt_template():
    """RA-45: OPTIMIZE_NO_JD_PROMPT renders resume content without a JD section."""
    from app.services.prompt.templates import OPTIMIZE_NO_JD_PROMPT

    messages = OPTIMIZE_NO_JD_PROMPT.format_messages(
        resume_content="Some resume content",
        template="modern",
    )
    human = messages[1].content

    assert "Some resume content" in human
    assert "Target Job Description" not in human


def test_optimize_with_jd_prompt_template():
    """RA-46: OPTIMIZE_WITH_JD_PROMPT renders both resume content and JD."""
    from app.services.prompt.templates import OPTIMIZE_WITH_JD_PROMPT

    messages = OPTIMIZE_WITH_JD_PROMPT.format_messages(
        resume_content="Some resume content",
        job_description="Senior Engineer at Google",
        template="modern",
    )
    human = messages[1].content

    assert "Some resume content" in human
    assert "Senior Engineer at Google" in human
    assert "Job Description" in human


def test_optimize_no_jd_prompt_template_empty_content_raises():
    """ChatPromptTemplate raises KeyError / ValueError on missing required variable."""
    import pytest
    from app.services.prompt.templates import OPTIMIZE_NO_JD_PROMPT

    with pytest.raises(Exception):
        OPTIMIZE_NO_JD_PROMPT.format_messages(template="modern")
