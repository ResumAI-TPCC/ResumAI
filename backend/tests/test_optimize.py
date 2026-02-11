"""
Tests for Optimize Resume Endpoint (RA-45, RA-46, RA-47)
"""

import base64
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.config import settings
from app.services.llm.base import LLMResponse


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
- Architected and developed 5 production web applications serving 10K+ daily users
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


@patch("app.services.resume_service.get_llm_provider")
@patch("app.services.resume_service.get_resume_content", new_callable=AsyncMock)
def test_optimize_resume_without_jd(mock_get_content, mock_get_provider, client):
    """RA-45: Test optimize and download without job description"""
    mock_get_content.return_value = MOCK_RESUME_TEXT

    mock_provider = MagicMock()
    mock_provider.optimize = AsyncMock(
        return_value=LLMResponse(content=MOCK_OPTIMIZED_WITHOUT_JD, model="test")
    )
    mock_get_provider.return_value = mock_provider

    response = client.post(
        f"{settings.API_PREFIX}/resume/optimize",
        json={"session_id": "test-session-123"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "encoded_file" in data
    assert "filename" in data
    assert data["filename"] == "optimized_resume.md"
    assert data["format"] == "markdown"

    # Verify base64 decoding works
    decoded = base64.b64decode(data["encoded_file"])
    content = decoded.decode("utf-8")

    assert "John Doe" in content
    assert "without JD" in content


@patch("app.services.resume_service.get_llm_provider")
@patch("app.services.resume_service.get_resume_content", new_callable=AsyncMock)
def test_optimize_resume_with_jd(mock_get_content, mock_get_provider, client):
    """RA-46: Test optimize and download with job description"""
    mock_get_content.return_value = MOCK_RESUME_TEXT

    mock_provider = MagicMock()
    mock_provider.optimize = AsyncMock(
        return_value=LLMResponse(content=MOCK_OPTIMIZED_WITH_JD, model="test")
    )
    mock_get_provider.return_value = mock_provider

    response = client.post(
        f"{settings.API_PREFIX}/resume/optimize",
        json={
            "session_id": "test-session-456",
            "job_description": "Senior Software Engineer position requiring microservices experience",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert "encoded_file" in data

    # Verify content indicates JD optimization
    decoded = base64.b64decode(data["encoded_file"])
    content = decoded.decode("utf-8")

    assert "with JD" in content
    assert "John Doe" in content


def test_optimize_resume_missing_session_id(client):
    """Test optimize endpoint requires session_id"""
    response = client.post(
        f"{settings.API_PREFIX}/resume/optimize",
        json={},
    )

    assert response.status_code == 422


def test_file_service_base64_encoding():
    """RA-47: Test file service encoding functions"""
    from app.services.file_service import generate_and_encode_resume

    test_content = "# Test Resume\n\nThis is a test."
    encoded = generate_and_encode_resume(test_content)

    # Verify it's valid base64
    decoded = base64.b64decode(encoded)
    assert decoded.decode("utf-8") == test_content


def test_prompt_builder_optimize_without_jd():
    """RA-45: Test prompt builder generates optimize prompt without JD"""
    from app.services.prompt.builder import get_prompt_builder

    builder = get_prompt_builder()
    prompt = builder.build_optimize_prompt("Some resume content")

    assert "Some resume content" in prompt
    assert "job description" not in prompt.lower() or "Job Description" not in prompt


def test_prompt_builder_optimize_with_jd():
    """RA-46: Test prompt builder generates optimize prompt with JD"""
    from app.services.prompt.builder import get_prompt_builder

    builder = get_prompt_builder()
    prompt = builder.build_optimize_prompt(
        "Some resume content", "Senior Engineer at Google"
    )

    assert "Some resume content" in prompt
    assert "Senior Engineer at Google" in prompt


def test_prompt_builder_optimize_empty_content():
    """Test prompt builder rejects empty resume content"""
    from app.services.prompt.builder import get_prompt_builder
    import pytest

    builder = get_prompt_builder()
    with pytest.raises(ValueError, match="resume_content cannot be empty"):
        builder.build_optimize_prompt("")
