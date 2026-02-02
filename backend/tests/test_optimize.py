"""
Tests for Optimize Resume Endpoint (RA-47)
"""

import base64

from app.core.config import settings


def test_optimize_resume_without_jd(client):
    """Test optimize and download without job description"""
    response = client.post(
        f"{settings.API_PREFIX}/resume/optimize",
        json={"session_id": "test-session-123"}
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
    
    assert "Resume" in content
    assert "test-session-123" in content
    assert "without JD" in content


def test_optimize_resume_with_jd(client):
    """Test optimize and download with job description"""
    response = client.post(
        f"{settings.API_PREFIX}/resume/optimize",
        json={
            "session_id": "test-session-456",
            "job_description": "Senior Software Engineer position"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "encoded_file" in data
    
    # Verify content indicates JD optimization
    decoded = base64.b64decode(data["encoded_file"])
    content = decoded.decode("utf-8")
    
    assert "with JD" in content
    assert "test-session-456" in content


def test_optimize_resume_missing_session_id(client):
    """Test optimize endpoint requires session_id"""
    response = client.post(
        f"{settings.API_PREFIX}/resume/optimize",
        json={}
    )
    
    assert response.status_code == 422


def test_file_service_base64_encoding():
    """Test file service encoding functions"""
    from app.services.file_service import generate_and_encode_resume
    
    test_content = "# Test Resume\n\nThis is a test."
    encoded = generate_and_encode_resume(test_content)
    
    # Verify it's valid base64
    decoded = base64.b64decode(encoded)
    assert decoded.decode("utf-8") == test_content
