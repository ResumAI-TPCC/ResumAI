"""
Tests for Resume Download Endpoint (RA-47)
"""

import io
from unittest.mock import MagicMock, patch

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
def mock_gcs_client():
    """Mock GCS client for download tests"""
    with patch("app.services.resume_service._get_gcs_client") as mock:
        client = MagicMock()
        bucket = MagicMock()
        blob = MagicMock()
        
        mock.return_value = client
        client.bucket.return_value = bucket
        bucket.blob.return_value = blob
        
        yield blob


def test_download_resume_success(client, mock_gcs_client, sample_pdf_content):
    """Test successful resume download (RA-47)"""
    # Mock blob exists and returns content
    mock_gcs_client.exists.return_value = True
    mock_gcs_client.download_as_bytes.return_value = sample_pdf_content
    mock_gcs_client.content_type = "application/pdf"
    
    # Create download request
    request_data = {
        "file_id": "test-file-id-123",
        "storage_path": f"gs://{settings.GCS_BUCKET_NAME}/test/test_resume.pdf",
    }
    
    response = client.post(f"{settings.API_PREFIX}/resume/download", json=request_data)
    
    assert response.status_code == 200
    assert response.content == sample_pdf_content
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers.get("content-disposition", "")
    assert "test_resume.pdf" in response.headers.get("content-disposition", "")


def test_download_resume_file_not_found(client, mock_gcs_client):
    """Test download when file doesn't exist in GCS"""
    # Mock blob doesn't exist
    mock_gcs_client.exists.return_value = False
    
    request_data = {
        "file_id": "nonexistent-file-id",
        "storage_path": f"gs://{settings.GCS_BUCKET_NAME}/test/nonexistent.pdf",
    }
    
    response = client.post(f"{settings.API_PREFIX}/resume/download", json=request_data)
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_download_resume_invalid_storage_path(client):
    """Test download with invalid storage path format"""
    # Invalid path (missing gs:// prefix)
    request_data = {
        "file_id": "test-file-id",
        "storage_path": "invalid/path/to/file.pdf",
    }
    
    response = client.post(f"{settings.API_PREFIX}/resume/download", json=request_data)
    
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


def test_download_resume_malformed_gcs_path(client):
    """Test download with malformed GCS path"""
    # Malformed GCS path (missing object path)
    request_data = {
        "file_id": "test-file-id",
        "storage_path": "gs://bucket-only",
    }
    
    response = client.post(f"{settings.API_PREFIX}/resume/download", json=request_data)
    
    assert response.status_code == 400


def test_download_resume_docx(client, mock_gcs_client):
    """Test downloading DOCX file"""
    from docx import Document
    
    # Create sample DOCX
    doc = Document()
    doc.add_paragraph("Jane Smith")
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    docx_content = buffer.read()
    
    # Mock blob exists and returns DOCX content
    mock_gcs_client.exists.return_value = True
    mock_gcs_client.download_as_bytes.return_value = docx_content
    mock_gcs_client.content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    request_data = {
        "file_id": "test-docx-id",
        "storage_path": f"gs://{settings.GCS_BUCKET_NAME}/test/resume.docx",
    }
    
    response = client.post(f"{settings.API_PREFIX}/resume/download", json=request_data)
    
    assert response.status_code == 200
    assert response.content == docx_content
    assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in response.headers["content-type"]
    assert "resume.docx" in response.headers.get("content-disposition", "")


def test_download_resume_gcs_error(client, mock_gcs_client):
    """Test download when GCS operation fails"""
    # Mock GCS download error
    mock_gcs_client.exists.return_value = True
    mock_gcs_client.download_as_bytes.side_effect = Exception("GCS connection error")
    
    request_data = {
        "file_id": "test-file-id",
        "storage_path": f"gs://{settings.GCS_BUCKET_NAME}/test/resume.pdf",
    }
    
    response = client.post(f"{settings.API_PREFIX}/resume/download", json=request_data)
    
    assert response.status_code == 500
    assert "failed to download" in response.json()["detail"].lower()


def test_download_resume_cache_headers(client, mock_gcs_client, sample_pdf_content):
    """Test that download response includes proper cache control headers"""
    mock_gcs_client.exists.return_value = True
    mock_gcs_client.download_as_bytes.return_value = sample_pdf_content
    mock_gcs_client.content_type = "application/pdf"
    
    request_data = {
        "file_id": "test-file-id",
        "storage_path": f"gs://{settings.GCS_BUCKET_NAME}/test/resume.pdf",
    }
    
    response = client.post(f"{settings.API_PREFIX}/resume/download", json=request_data)
    
    assert response.status_code == 200
    assert "no-cache" in response.headers.get("cache-control", "").lower()
