"""
Resume Service Layer

RA-23: Upload resume to GCS and return file_id
RA-24: Parse resume file and extract structured data
"""

from __future__ import annotations

import re
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from docx import Document
from fastapi import HTTPException, UploadFile, status
from google.cloud import storage
from pypdf import PdfReader
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.schemas.resume_schema import (
    ContactInfo,
    Education,
    ResumeData,
    ResumeUploadResponse,
    WorkExperience,
)

# Configuration
ALLOWED_EXTS = {".pdf", ".doc", ".docx", ".txt"}
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10MB

# Global GCS client instance for reuse
_gcs_client: Optional[storage.Client] = None


# ============================================================================
# RA-23: GCS Upload Functions
# ============================================================================


def _get_gcs_client() -> storage.Client:
    """Get or create a GCS client instance."""
    global _gcs_client
    if _gcs_client is not None:
        return _gcs_client

    # Use Application Default Credentials (ADC)
    _gcs_client = storage.Client(project=settings.GCP_PROJECT_ID or None)
    return _gcs_client


def _validate_filename(filename: str) -> None:
    """Validate file extension and name."""
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename"
        )

    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {ext}. Allowed: {sorted(ALLOWED_EXTS)}",
        )


def _build_object_name(file_id: str, filename: str) -> str:
    """Build GCS object path."""
    safe_name = Path(filename).name
    prefix = settings.GCS_OBJECT_PREFIX.strip("/")
    if prefix:
        return f"{prefix}/{file_id}/{safe_name}"
    return f"{file_id}/{safe_name}"


async def _read_file_content(file: UploadFile) -> bytes:
    """Read file content with size limit check."""
    size = 0
    chunks = []
    try:
        while True:
            chunk = await file.read(1024 * 1024)  # 1MB
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_SIZE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File too large. Max {MAX_SIZE_BYTES // (1024 * 1024)}MB",
                )
            chunks.append(chunk)
    finally:
        await file.close()
    return b"".join(chunks)


def _do_gcs_upload(
    content: bytes, object_name: str, content_type: Optional[str]
) -> None:
    """Synchronous GCS upload operation."""
    if not settings.GCS_BUCKET_NAME:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GCS bucket not configured",
        )

    client = _get_gcs_client()
    bucket = client.bucket(settings.GCS_BUCKET_NAME)
    blob = bucket.blob(object_name)
    blob.upload_from_string(
        content, content_type=content_type or "application/octet-stream"
    )


# ============================================================================
# RA-24: File Parsing Functions
# ============================================================================


def _extract_text_from_pdf(file_path: Path) -> str:
    """Extract text from PDF file"""
    try:
        reader = PdfReader(file_path)
        text_parts = []

        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)

        return "\n".join(text_parts)
    except Exception as e:
        print(f"PDF parsing error: {str(e)}")
        raise ValueError("Failed to parse PDF file")


def _extract_text_from_docx(file_path: Path) -> str:
    """Extract text from DOCX file"""
    try:
        doc = Document(file_path)
        text_parts = []

        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)

        return "\n".join(text_parts)
    except Exception as e:
        print(f"DOCX parsing error: {str(e)}")
        raise ValueError("Failed to parse DOCX file")


def _extract_structured_data(raw_text: str, filename: str) -> ResumeData:
    """
    Extract structured information from raw text using regex patterns

    Note: This is a basic implementation using regex.
    For production, consider using NLP or LLM-based extraction.
    """
    # Extract email
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    emails = re.findall(email_pattern, raw_text)
    email = emails[0] if emails else None

    # Extract phone number with validation
    phone_pattern = r"\b(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}\b"
    raw_phones = re.findall(phone_pattern, raw_text)
    # Filter to valid phone numbers (7-15 digits)
    phones = [p for p in raw_phones if 7 <= len(re.sub(r"\D", "", p)) <= 15]
    phone = phones[0] if phones else None

    # Extract LinkedIn URL
    linkedin_pattern = r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+"
    linkedin_urls = re.findall(linkedin_pattern, raw_text, re.IGNORECASE)
    linkedin = linkedin_urls[0] if linkedin_urls else None

    # Extract name (first non-empty line, often the name)
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    full_name = lines[0] if lines else None

    # Extract skills (keywords after "Skills" section)
    skills = _extract_skills(raw_text)

    # Extract education
    education = _extract_education(raw_text)

    # Extract work experience
    work_experience = _extract_work_experience(raw_text)

    # Extract summary
    summary = _extract_summary(raw_text)

    contact_info = ContactInfo(
        email=email,
        phone=phone,
        linkedin=linkedin,
        location=None,
    )

    return ResumeData(
        full_name=full_name,
        contact_info=contact_info,
        summary=summary,
        skills=skills,
        education=education,
        work_experience=work_experience,
        raw_text=raw_text,
    )


def _extract_skills(text: str) -> list[str]:
    """Extract skills from resume text"""
    skills = []

    # Look for skills section
    skills_pattern = r"(?:skills?|technical skills?|core competencies)[\s:]*\n((?:[^\n]+\n?)+?)(?:\n\n|experience|employment|work history|education|$)"
    match = re.search(skills_pattern, text, re.IGNORECASE | re.DOTALL)

    if match:
        skills_text = match.group(1)
        # Split by common separators
        skill_items = re.split(r"[,;•·\|]|\n", skills_text)
        skills = [s.strip() for s in skill_items if s.strip() and len(s.strip()) > 2]

    # Limit to first 20 skills
    return skills[:20]


def _extract_education(text: str) -> list[Education]:
    """Extract education information"""
    education_list = []

    # Look for education section
    edu_pattern = r"(?:education|academic background)[\s:]*\n((?:[^\n]+\n?)+?)(?:\n\n|experience|skills|$)"
    match = re.search(edu_pattern, text, re.IGNORECASE | re.DOTALL)

    if match:
        edu_text = match.group(1)
        raw_lines = edu_text.split("\n")

        # Intelligent field classification with flexible entry boundaries
        current_entry = []
        for raw_line in raw_lines:
            line = raw_line.strip()
            # Blank line indicates end of one education entry
            if not line:
                if current_entry:
                    education_list.append(
                        _classify_education_fields(current_entry)
                    )
                    current_entry = []
                continue

            current_entry.append(line)

        # Process remaining partial entry (if text didn't end with a blank line)
        if current_entry:
            education_list.append(
                _classify_education_fields(current_entry)
            )

    return education_list[:5]  # Limit to 5 entries


def _classify_education_fields(entry_lines: list[str]) -> Education:
    """Classify education entry fields by content patterns"""
    institution = None
    degree = None
    field = None

    for line in entry_lines:
        lower_line = line.lower()
        if institution is None and re.search(r"\b(university|college|institute|school)\b", lower_line):
            institution = line
        elif degree is None and re.search(r"\b(bachelor|master|ph\.?d|phd|b\.?sc|m\.?sc|ba|bs|beng|meng|mba)\b", lower_line):
            degree = line
        elif field is None:
            field = line

    # Fallback to positional mapping if classification failed
    if institution is None and len(entry_lines) > 0:
        institution = entry_lines[0]
    if degree is None and len(entry_lines) > 1:
        degree = entry_lines[1]
    if field is None and len(entry_lines) > 2:
        field = entry_lines[2]

    return Education(institution=institution, degree=degree, field=field)


def _extract_work_experience(text: str) -> list[WorkExperience]:
    """Extract work experience information"""
    experience_list = []

    # Look for experience section
    exp_pattern = r"(?:experience|employment|work history)[\s:]*\n((?:[^\n]+\n?)+?)(?:\n\n|education|skills|$)"
    match = re.search(exp_pattern, text, re.IGNORECASE | re.DOTALL)

    if match:
        exp_text = match.group(1)
        lines = [line.strip() for line in exp_text.split("\n") if line.strip()]

        # Simple heuristic: company, position, duration pattern
        current_entry = []
        for line in lines:
            current_entry.append(line)
            if len(current_entry) >= 3:
                experience_list.append(
                    WorkExperience(
                        company=current_entry[0] if len(current_entry) > 0 else None,
                        position=current_entry[1] if len(current_entry) > 1 else None,
                        duration=current_entry[2] if len(current_entry) > 2 else None,
                    )
                )
                current_entry = []

    return experience_list[:10]  # Limit to 10 entries


def _extract_summary(text: str) -> Optional[str]:
    """Extract professional summary"""
    # Look for summary/objective section
    summary_pattern = r"(?:summary|objective|profile|about)[\s:]*\n((?:[^\n]+\n?)+?)(?:\n\n|experience|employment|work history|education|skills|$)"
    match = re.search(summary_pattern, text, re.IGNORECASE | re.DOTALL)

    if match:
        summary = match.group(1).strip()
        # Limit length
        return summary[:500] if len(summary) > 500 else summary

    return None


async def _parse_file_from_bytes(
    file_content: bytes, filename: str
) -> ResumeData:
    """
    Parse resume from memory buffer

    Args:
        file_content: File content as bytes
        filename: Original filename

    Returns:
        ResumeData: Extracted resume information
    """
    # Security: Extract only the basename to prevent path traversal
    safe_filename = Path(filename).name

    # Validate filename for unsafe characters (e.g., null bytes, control chars)
    if "\x00" in safe_filename or any(ord(ch) < 32 for ch in safe_filename):
        raise ValueError("Invalid filename")

    # Determine file extension from safe filename
    if safe_filename.endswith(".pdf"):
        suffix = ".pdf"
    elif safe_filename.endswith(".docx"):
        suffix = ".docx"
    elif safe_filename.endswith(".txt"):
        suffix = ".txt"
    else:
        raise ValueError(f"Unsupported file format: {safe_filename}")

    # For PDF/DOCX, we need to use temporary file
    if suffix in [".pdf", ".docx"]:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(file_content)
            tmp.flush()
            tmp_path = Path(tmp.name)

        try:
            # Extract text based on file type
            if suffix == ".pdf":
                raw_text = _extract_text_from_pdf(tmp_path)
            else:  # .docx
                raw_text = _extract_text_from_docx(tmp_path)

            return _extract_structured_data(raw_text, safe_filename)
        finally:
            tmp_path.unlink(missing_ok=True)
    else:
        # For text files, parse directly
        raw_text = file_content.decode("utf-8", errors="ignore")
        return _extract_structured_data(raw_text, safe_filename)


# ============================================================================
# Main Integration Function
# ============================================================================


async def upload_and_parse_resume(file: UploadFile) -> ResumeUploadResponse:
    """
    Upload resume to GCS and attempt to parse it (RA-23 + RA-24).

    Always uploads the file and returns file_id + storage_path (RA-23).
    Attempts to parse and returns parsed_data if successful (RA-24).

    Args:
        file: Resume file to upload and parse

    Returns:
        ResumeUploadResponse:
            - file_id: Session ID from GCS upload (always present)
            - filename: Original filename (always present)
            - storage_path: GCS storage path (always present)
            - parsed_data: Extracted resume data (only if parsing succeeded)

    Raises:
        HTTPException: On file validation or GCS upload errors
    """
    # Step 1: Validate filename (RA-23)
    _validate_filename(file.filename)

    if not settings.GCS_BUCKET_NAME:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GCS bucket not configured",
        )

    # Step 2: Generate file ID and read file content
    file_id = str(uuid.uuid4())
    object_name = _build_object_name(file_id, file.filename)

    # Read file content with size validation
    content = await _read_file_content(file)

    # Step 3: Upload to GCS (RA-23)
    try:
        await run_in_threadpool(
            _do_gcs_upload,
            content=content,
            object_name=object_name,
            content_type=file.content_type,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GCS upload failed: {exc}",
        ) from exc

    storage_path = f"gs://{settings.GCS_BUCKET_NAME}/{object_name}"

    # Step 4: Attempt to parse file (RA-24)
    parsed_data: Optional[ResumeData] = None
    try:
        parsed_data = await _parse_file_from_bytes(
            file_content=content,
            filename=file.filename,
        )
    except Exception as e:
        # Log parsing error but don't fail the upload
        print(f"Resume parsing error: {str(e)}")
        # parsed_data remains None

    # Step 5: Return response with upload info (always) + parse data (if successful)
    return ResumeUploadResponse(
        file_id=file_id,
        filename=file.filename,
        storage_path=storage_path,
        parsed_data=parsed_data,
    )
