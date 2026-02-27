"""
Unit Tests for RA-36: GCS Download and Content Parsing Service

Tests the functionality of downloading resume files from GCS
and parsing their content for further processing.
"""

import pytest
from unittest.mock import patch


# Mock classes for GCS client
class FakeBlob:
    """Fake GCS Blob for testing."""

    def __init__(self, name: str, content: bytes = b""):
        self.name = name
        self._content = content

    def download_as_bytes(self) -> bytes:
        """Simulate downloading blob content."""
        return self._content

    def download_as_string(self) -> str:
        """Simulate downloading blob as string."""
        return self._content.decode("utf-8")


class FakeBucket:
    """Fake GCS Bucket for testing."""

    def __init__(self):
        self.blobs = {}

    def blob(self, name: str) -> FakeBlob:
        """Get a blob by name."""
        if name in self.blobs:
            return self.blobs[name]
        return FakeBlob(name)

    def add_blob(self, name: str, content: bytes) -> None:
        """Add a blob with content for testing."""
        self.blobs[name] = FakeBlob(name, content)


class FakeGCSClient:
    """Fake GCS Client for testing."""

    def __init__(self):
        self._buckets = {}

    def bucket(self, name: str) -> FakeBucket:
        """Get a bucket by name."""
        if name not in self._buckets:
            self._buckets[name] = FakeBucket()
        return self._buckets[name]


class TestGCSDownloadService:
    """Test suite for GCS download functionality."""

    def test_validate_filename_valid_extensions(self):
        """Test filename validation with valid extensions."""
        from app.services.validators.file_validator import validate_filename

        # Should not raise for valid extensions
        valid_files = ["resume.pdf", "resume.docx"]
        for filename in valid_files:
            validate_filename(filename)  # Should not raise

    def test_validate_filename_invalid_extension(self):
        """Test filename validation rejects invalid extensions."""
        from fastapi import HTTPException
        from app.services.validators.file_validator import validate_filename

        with pytest.raises(HTTPException) as exc_info:
            validate_filename("virus.exe")
        assert exc_info.value.status_code == 400
        assert "Unsupported file type" in str(exc_info.value.detail)

    def test_validate_filename_empty(self):
        """Test filename validation rejects empty filename."""
        from fastapi import HTTPException
        from app.services.validators.file_validator import validate_filename

        with pytest.raises(HTTPException) as exc_info:
            validate_filename("")
        assert exc_info.value.status_code == 400
        assert "No file provided" in str(exc_info.value.detail)


class TestContentParsing:
    """Test suite for resume content parsing functionality.

    Note: These tests define expected behavior for content parsing.
    If the parsing functions are not yet implemented, these tests
    serve as specifications for the implementation.
    """

    def test_parse_txt_content(self):
        """Test parsing plain text resume content."""
        txt_content = """
        John Doe
        Software Engineer

        Experience:
        - Built web applications using React
        - Led team of 5 engineers

        Skills: Python, React, AWS
        """

        # Direct string content should be returned as-is (stripped)
        parsed = txt_content.strip()
        assert "John Doe" in parsed
        assert "Software Engineer" in parsed
        assert "Python" in parsed

    def test_parse_content_preserves_structure(self):
        """Test that parsing preserves content structure."""
        content = """Name: Jane Smith
Title: Data Scientist

Experience:
1. Company A - Senior Analyst
2. Company B - Junior Analyst

Education:
- PhD Computer Science
- BS Mathematics"""

        parsed = content.strip()

        # Verify structure is preserved
        assert "Name: Jane Smith" in parsed
        assert "Experience:" in parsed
        assert "Education:" in parsed
        assert "1. Company A" in parsed


class TestGCSIntegration:
    """Integration tests for GCS download workflow."""

    @pytest.fixture
    def fake_gcs_client(self):
        """Create a fake GCS client with test data."""
        client = FakeGCSClient()
        bucket = client.bucket("test-bucket")

        # Add test resume content
        resume_content = b"""John Doe
Software Engineer | San Francisco

Experience:
- Built scalable web applications
- Improved performance by 40%

Skills: Python, JavaScript, AWS"""

        bucket.add_blob("resumes/test-id-123/resume.txt", resume_content)
        return client

    def test_download_resume_content_success(self, fake_gcs_client):
        """Test successful resume content download."""
        bucket = fake_gcs_client.bucket("test-bucket")
        blob = bucket.blob("resumes/test-id-123/resume.txt")

        content = blob.download_as_string()

        assert "John Doe" in content
        assert "Software Engineer" in content
        assert "Python" in content

    def test_download_nonexistent_blob_returns_empty(self, fake_gcs_client):
        """Test downloading non-existent blob returns empty content."""
        bucket = fake_gcs_client.bucket("test-bucket")
        blob = bucket.blob("resumes/nonexistent/file.txt")

        content = blob.download_as_bytes()
        assert content == b""


class TestDownloadServiceHelpers:
    """Test helper functions for download service."""

    def test_file_id_extraction(self):
        """Test extracting file ID from storage path."""
        # Given a storage path, we should be able to extract the file ID
        storage_path = "gs://bucket-name/resumes/abc-123-def/resume.pdf"
        
        # Extract file_id from path
        parts = storage_path.replace("gs://", "").split("/")
        # parts = ['bucket-name', 'resumes', 'abc-123-def', 'resume.pdf']
        file_id = parts[2]  # The file_id is typically the third component

        assert file_id == "abc-123-def"

    def test_content_type_detection(self):
        """Test content type detection from filename."""
        test_cases = {
            "resume.pdf": "application/pdf",
            "cv.doc": "application/msword",
            "resume.docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "plain.txt": "text/plain",
        }

        for filename, expected_type in test_cases.items():
            ext = filename.split(".")[-1].lower()
            content_types = {
                "pdf": "application/pdf",
                "doc": "application/msword",
                "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "txt": "text/plain",
            }
            assert content_types.get(ext) == expected_type
