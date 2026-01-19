"""
Tests for Resume Upload Endpoint (RA-24)
"""

import io
import pytest

from app.core.config import settings


@pytest.fixture
def sample_pdf_content():
    """Create sample PDF content"""
    return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Contents 4 0 R
/MediaBox [0 0 612 792]
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(John Doe) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000214 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
306
%%EOF"""


@pytest.fixture
def sample_docx_content():
    """Create sample DOCX content"""
    from docx import Document
    
    doc = Document()
    doc.add_paragraph("Jane Smith")
    doc.add_paragraph("jane.smith@example.com")
    doc.add_paragraph("+1-555-1234")
    doc.add_paragraph("Skills: Python, FastAPI, Docker")
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.read()


def test_upload_resume_pdf_success(client, sample_pdf_content):
    """Test successful PDF upload and parsing"""
    files = {"file": ("test_resume.pdf", sample_pdf_content, "application/pdf")}
    
    response = client.post(f"{settings.api_prefix}/resume/", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["message"] == "Resume parsed successfully"
    assert data["file_type"] == "pdf"
    assert "data" in data
    assert data["data"] is not None
    assert "processing_time_ms" in data


def test_upload_resume_docx_success(client, sample_docx_content):
    """Test successful DOCX upload and parsing"""
    files = {"file": ("test_resume.docx", sample_docx_content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    
    response = client.post(f"{settings.api_prefix}/resume/", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["file_type"] == "docx"
    parsed_data = data["data"]
    assert parsed_data["contact_info"]["email"] == "jane.smith@example.com"


def test_upload_resume_unsupported_format(client):
    """Test upload with unsupported file format"""
    files = {"file": ("test.exe", b"fake exe content", "application/x-msdownload")}
    
    response = client.post(f"{settings.api_prefix}/resume/", files=files)
    
    assert response.status_code == 400
    assert "unsupported" in response.json()["detail"].lower()


def test_upload_resume_file_too_large(client):
    """Test upload with file exceeding size limit"""
    # Create a file larger than 10MB
    large_content = b"x" * (11 * 1024 * 1024)
    files = {"file": ("large.pdf", large_content, "application/pdf")}
    
    response = client.post(f"{settings.api_prefix}/resume/", files=files)
    
    assert response.status_code == 400
    assert "too large" in response.json()["detail"].lower()


def test_upload_resume_invalid_filename(client, sample_pdf_content):
    """Test upload with invalid filename (path traversal attempt)"""
    malicious_filenames = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "../../test.pdf",
    ]
    
    for filename in malicious_filenames:
        files = {"file": (filename, sample_pdf_content, "application/pdf")}
        response = client.post(f"{settings.api_prefix}/resume/", files=files)
        
        # Should either reject the filename or sanitize it
        # We accept sanitized version, so check that it succeeds with safe name
        if response.status_code == 200:
            # Filename was sanitized successfully
            assert response.json()["success"] is True
        else:
            # Filename was rejected
            assert response.status_code == 400


def test_upload_resume_text_file(client):
    """Test upload with text file"""
    text_content = b"John Doe\njohn@example.com\n+1-555-0000"
    files = {"file": ("resume.txt", text_content, "text/plain")}
    
    response = client.post(f"{settings.api_prefix}/resume/", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["file_type"] == "txt"


def test_match_endpoint_placeholder(client):
    """Test match endpoint returns placeholder response"""
    response = client.post(f"{settings.api_prefix}/resume/match")
    
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_optimize_endpoint_placeholder(client):
    """Test optimize endpoint returns placeholder response"""
    response = client.post(f"{settings.api_prefix}/resume/optimize")
    
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_endpoint_placeholder(client):
    """Test analyze endpoint returns placeholder response"""
    response = client.post(f"{settings.api_prefix}/resume/analyze")
    
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
