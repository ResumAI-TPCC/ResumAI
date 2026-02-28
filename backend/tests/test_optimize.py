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

    # Verify base64 decoding works and returns valid PDF
    decoded = base64.b64decode(data["data"]["encoded_file"])
    assert decoded[:4] == b'%PDF', "Response should be a valid PDF file"
    assert len(decoded) > 100, "PDF file should not be empty"


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

    # Verify response is a valid PDF file
    decoded = base64.b64decode(data["data"]["encoded_file"])
    assert decoded[:4] == b'%PDF', "Response should be a valid PDF file"
    assert len(decoded) > 100, "PDF file should not be empty"


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
    # Should NOT contain JD section
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
    from app.services.prompt.builder import get_prompt_builder
    import pytest

    builder = get_prompt_builder()
    with pytest.raises(ValueError, match="resume_content cannot be empty"):
        builder.build_optimize_prompt("")
