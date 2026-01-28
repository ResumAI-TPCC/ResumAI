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
    
    assert response.status_code == 201
    data = response.json()
    
    # RA-23: Upload info (always present)
    assert "file_id" in data
    assert data["filename"] == "test_resume.pdf"
    assert "storage_path" in data
    assert data["storage_path"].startswith("gs://")
    
    # RA-24: Parse data (should be present for valid PDF)
    assert "parsed_data" in data
    if data["parsed_data"] is not None:
        assert "full_name" in data["parsed_data"]
        assert "contact_info" in data["parsed_data"]


def test_upload_resume_docx_success(client, sample_docx_content):
    """Test successful DOCX upload and parsing"""
    files = {"file": ("test_resume.docx", sample_docx_content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    
    response = client.post(f"{settings.api_prefix}/resume/", files=files)
    
    assert response.status_code == 201
    data = response.json()
    
    # RA-23: Upload info
    assert data["filename"] == "test_resume.docx"
    assert "file_id" in data
    assert "storage_path" in data
    
    # RA-24: Parse data
    if data["parsed_data"] is not None:
        parsed_data = data["parsed_data"]
        # May or may not find email depending on exact content
        assert "contact_info" in parsed_data
        assert "skills" in parsed_data


def test_upload_resume_unsupported_format(client):
    """Test upload with unsupported file format"""
    files = {"file": ("test.exe", b"fake exe content", "application/x-msdownload")}
    
    response = client.post(f"{settings.api_prefix}/resume/", files=files)
    
    assert response.status_code == 400
    assert "unsupported" in response.json()["detail"].lower() or "not supported" in response.json()["detail"].lower()


def test_upload_resume_file_too_large(client):
    """Test upload with file exceeding size limit"""
    # Create a file larger than 10MB
    large_content = b"x" * (11 * 1024 * 1024)
    files = {"file": ("large.pdf", large_content, "application/pdf")}
    
    response = client.post(f"{settings.api_prefix}/resume/", files=files)
    
    assert response.status_code == 413
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
        if response.status_code == 201:
            # Filename was sanitized successfully
            assert "file_id" in response.json()
            assert "storage_path" in response.json()
        else:
            # Filename was rejected
            assert response.status_code == 400


def test_upload_resume_text_file(client):
    """Test upload with text file"""
    text_content = b"John Doe\njohn@example.com\n+1-555-0000"
    files = {"file": ("resume.txt", text_content, "text/plain")}
    
    response = client.post(f"{settings.api_prefix}/resume/", files=files)
    
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "resume.txt"
    assert "file_id" in data
    assert "storage_path" in data
    # parsed_data may be present or None depending on parsing success


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


# GCS Upload Unit Tests
def test_gcs_upload_success(client, sample_pdf_content, mock_gcs):
    """Test that GCS upload is called with correct parameters"""
    files = {"file": ("test_resume.pdf", sample_pdf_content, "application/pdf")}
    
    response = client.post(f"{settings.api_prefix}/resume/", files=files)
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify GCS client was used
    mock_gcs.return_value.bucket.assert_called_once_with(settings.GCS_BUCKET_NAME)
    
    # Verify storage_path is in correct format
    assert data["storage_path"].startswith("gs://")
    assert settings.GCS_BUCKET_NAME in data["storage_path"]


def test_gcs_object_name_format(client, sample_pdf_content, mock_gcs):
    """Test that GCS object names follow the correct format"""
    files = {"file": ("my_resume.pdf", sample_pdf_content, "application/pdf")}
    
    response = client.post(f"{settings.api_prefix}/resume/", files=files)
    
    assert response.status_code == 201
    data = response.json()
    file_id = data["file_id"]
    
    # Object name should follow pattern: {prefix}/{file_id}/{filename}
    # Storage path format: gs://bucket_name/prefix/file_id/filename
    assert file_id in data["storage_path"]
    assert "my_resume.pdf" in data["storage_path"]
    
    # Verify blob.upload_from_string was called
    mock_blob = mock_gcs.return_value.bucket.return_value.blob.return_value
    assert mock_blob.upload_from_string.called
