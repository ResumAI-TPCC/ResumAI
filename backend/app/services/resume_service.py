"""
Resume Service Layer

RA-23: Upload resume to GCS and return file_id
RA-24: Parse resume file and extract structured data
"""

from __future__ import annotations

import base64
import io
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import docx
from fastapi import HTTPException, UploadFile, status
from google.cloud import storage
from google.oauth2 import service_account
from pypdf import PdfReader
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.schemas.resume_schema import (
    ContactInfo,
    Education,
    ResumeData,
    ResumeUploadResponse,
    ResumeUploadData,
    WorkExperience,
)
from app.core.error_templates import (
    INVALID_SESSION_ID,
    SESSION_EXPIRED,
    SESSION_NOT_FOUND,
    INVALID_FILE_TYPE,
    MISSING_FILE,
    SCANNED_PDF_NOT_SUPPORTED,
    INVALID_PDF_FORMAT,
    PDF_READ_ERROR,
    EMPTY_FILE,
    GCS_UPLOAD_FAILED,
    GCS_BUCKET_NOT_FOUND,
)

# Configuration - Supported file types per design doc
ALLOWED_EXTS = {".pdf", ".docx", ".doc", ".txt"}

# UUID validation pattern
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)


# ============================================================================
# Session Validation Functions
# ============================================================================


def _validate_session_id(session_id: str) -> None:
    """Validate session ID is a proper UUID format to prevent path traversal attacks.
    
    Args:
        session_id: Session ID to validate
        
    Raises:
        HTTPException(400): If session_id is not a valid UUID format
    """
    if not session_id or not UUID_PATTERN.match(session_id):
        raise HTTPException(
            status_code=INVALID_SESSION_ID.code,
            detail=INVALID_SESSION_ID.detail,
        )


def _validate_session_expiry(blob: storage.Blob) -> None:
    """Validate that the session has not expired based on blob metadata.
    
    Args:
        blob: GCS blob containing the resume file
        
    Raises:
        HTTPException(404): If session has expired
    """
    if not blob.metadata:
        # If no metadata, assume it's an old file without expiration - allow it
        return
    
    expire_at_str = blob.metadata.get("expire_at")
    if not expire_at_str:
        # No expiration set, allow it
        return
    
    try:
        expire_at = datetime.fromisoformat(expire_at_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        
        if now > expire_at:
            raise HTTPException(
                status_code=SESSION_EXPIRED.code,
                detail=SESSION_EXPIRED.detail,
            )
    except ValueError as e:
        # Invalid date format in metadata, log but allow access
        # (Don't break functionality due to metadata issues)
        pass


# ============================================================================
# RA-23: GCS Upload Functions
# ============================================================================


def _get_gcs_client() -> storage.Client:
    """
    Create a new GCS client instance for each operation.
    
    The Google Cloud Storage SDK handles connection pooling internally,
    so creating new client instances per operation is efficient and avoids
    global state management issues.
    
    Returns:
        storage.Client: New GCS client instance
    """
    credentials = _build_service_account_credentials()

    # Use Application Default Credentials (ADC) if no explicit credentials provided
    if credentials is not None:
        return storage.Client(
            project=settings.GCP_PROJECT_ID or None, credentials=credentials
        )
    else:
        return storage.Client(project=settings.GCP_PROJECT_ID or None)


def _validate_filename(filename: str) -> None:
    """Validate file extension and name."""
    if not filename:
        raise HTTPException(
            status_code=MISSING_FILE.code, detail=MISSING_FILE.detail
        )

    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(
            status_code=INVALID_FILE_TYPE.code,
            detail=INVALID_FILE_TYPE.detail,
        )


def _clean_filename(filename: str) -> str:
    """
    Basic filename cleaning to remove unsafe characters.
    Replaces spaces and non-alphanumeric (except . - _) with underscores.
    """
    path = Path(filename)
    stem = path.stem
    ext = path.suffix

    # Replace non-alphanumeric/space/dash with nothing, then spaces/dashes with underscore
    clean_stem = re.sub(r"[^\w\s-]", "", stem).strip()
    clean_stem = re.sub(r"[-\s]+", "_", clean_stem)

    # Fallback if stem becomes empty
    if not clean_stem:
        clean_stem = "resume"

    return f"{clean_stem}{ext}"


def _validate_pdf_content(content: bytes) -> None:
    """
    Check if PDF is text-based. Rejects scanned PDFs (no extractable text).
    Used during upload validation.
    """
    try:
        reader = PdfReader(io.BytesIO(content))
        has_text = False
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                has_text = True
                break

        if not has_text:
            raise HTTPException(
                status_code=SCANNED_PDF_NOT_SUPPORTED.code,
                detail=SCANNED_PDF_NOT_SUPPORTED.detail,
            )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except (IOError, OSError) as exc:
        # File I/O errors
        raise HTTPException(
            status_code=PDF_READ_ERROR.code,
            detail=PDF_READ_ERROR.detail,
        ) from exc
    except ValueError as exc:
        # PDF parsing errors
        raise HTTPException(
            status_code=INVALID_PDF_FORMAT.code,
            detail=INVALID_PDF_FORMAT.detail,
        ) from exc
    except Exception as exc:
        # Unexpected errors
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"PDF validation failed: {str(exc)}",
        ) from exc


def _parse_pdf_to_text(content: bytes) -> str:
    """Parse text-based PDF to plain text."""
    try:
        reader = PdfReader(io.BytesIO(content))
        full_text = []
        for page in reader.pages:
            text = page.extract_text() or ""
            full_text.append(text)
        
        result = "\n".join(full_text).strip()
        if not result:
            raise HTTPException(
                status_code=SCANNED_PDF_NOT_SUPPORTED.code,
                detail=SCANNED_PDF_NOT_SUPPORTED.detail,
            )
        return result
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except (IOError, OSError) as exc:
        # File I/O errors
        raise HTTPException(
            status_code=PDF_READ_ERROR.code,
            detail=PDF_READ_ERROR.detail,
        ) from exc
    except ValueError as exc:
        # PDF parsing/format errors
        raise HTTPException(
            status_code=INVALID_PDF_FORMAT.code,
            detail=INVALID_PDF_FORMAT.detail,
        ) from exc
    except Exception as exc:
        # Unexpected errors
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"PDF parsing error: {str(exc)}",
        ) from exc


def _parse_docx_to_markdown(content: bytes) -> str:
    """Parse DOCX to simple Markdown (headings, paragraphs, lists, bold)."""
    try:
        doc = docx.Document(io.BytesIO(content))
        md_lines = []
        
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            
            # Simple style to markdown mapping
            style_name = para.style.name.lower()
            if style_name.startswith('heading 1'):
                md_lines.append(f"# {text}")
            elif style_name.startswith('heading 2'):
                md_lines.append(f"## {text}")
            elif style_name.startswith('heading 3'):
                md_lines.append(f"### {text}")
            elif para.style.name.startswith('List'):
                md_lines.append(f"* {text}")
            else:
                # Process inline formatting like bold
                processed_text = ""
                for run in para.runs:
                    run_text = run.text
                    if run.bold:
                        processed_text += f"**{run_text}**"
                    else:
                        processed_text += run_text
                md_lines.append(processed_text)
        
        result = "\n\n".join(md_lines).strip()
        if not result:
            raise HTTPException(
                status_code=EMPTY_FILE.code,
                detail=EMPTY_FILE.detail,
            )
        return result
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except (IOError, OSError) as exc:
        # File I/O errors
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not read DOCX file: {str(exc)}",
        ) from exc
    except (AttributeError, KeyError) as exc:
        # DOCX structure/format errors
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid DOCX format: {str(exc)}",
        ) from exc
    except Exception as exc:
        # Unexpected errors
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"DOCX parsing error: {str(exc)}",
        ) from exc


def _parse_doc_to_text(content: bytes) -> str:
    """Parse legacy .doc file by extracting readable text from binary content."""
    try:
        import olefile
        ole = olefile.OleFileIO(io.BytesIO(content))
        # WordDocument stream contains the raw text in .doc files
        if ole.exists("WordDocument"):
            stream = ole.openstream("WordDocument")
            raw = stream.read()
            text = raw.decode("utf-8", errors="ignore")
            result = "".join(
                c if c.isprintable() or c in "\n\r\t" else " " for c in text
            ).strip()
            if result:
                return result
        # Fallback: try to read any text from all streams
        text = content.decode("utf-8", errors="ignore")
        result = "".join(
            c if c.isprintable() or c in "\n\r\t" else " " for c in text
        ).strip()
        if result:
            return result
        raise ValueError("No text extracted")
    except ImportError:
        # olefile not installed: brute-force text extraction
        text = content.decode("utf-8", errors="ignore")
        result = "".join(
            c if c.isprintable() or c in "\n\r\t" else " " for c in text
        ).strip()
        if not result:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed to parse .doc file. Please convert to .docx format.",
            )
        return result
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse .doc file: {exc}. Please convert to .docx format.",
        ) from exc


async def get_resume_content(session_id: str) -> str:
    """
    Retrieve resume file from GCS by session_id and return extracted text.
    Validates session ID format and expiration before retrieval.
    
    Args:
        session_id: UUID session identifier
        
    Returns:
        str: Extracted text content from resume
        
    Raises:
        HTTPException(400): Invalid session ID format
        HTTPException(404): Session expired or not found
        HTTPException(422): Unsupported file type
    """
    # Validate session ID format to prevent path traversal
    _validate_session_id(session_id)
    
    client = _get_gcs_client()
    bucket = client.bucket(settings.GCS_BUCKET_NAME)
    
    # List blobs with the session prefix to find the file
    prefix = f"{settings.GCS_OBJECT_PREFIX.strip('/')}/{session_id}/"
    blobs = list(client.list_blobs(bucket, prefix=prefix))
    
    if not blobs:
        raise HTTPException(
            status_code=SESSION_NOT_FOUND.code,
            detail=SESSION_NOT_FOUND.detail,
        )
    
    # Strategy: Take the first found file in the session directory
    target_blob = blobs[0]
    
    # Validate session has not expired 
    _validate_session_expiry(target_blob)
    
    filename = target_blob.name
    content_bytes = await run_in_threadpool(target_blob.download_as_bytes)
    
    # Branching based on file extension
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return await run_in_threadpool(_parse_pdf_to_text, content_bytes)
    elif ext == ".docx":
        return await run_in_threadpool(_parse_docx_to_markdown, content_bytes)
    elif ext == ".doc":
        return await run_in_threadpool(_parse_doc_to_text, content_bytes)
    elif ext == ".txt":
        return content_bytes.decode("utf-8", errors="replace")
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type in storage: {ext}",
        )


def _build_object_name(file_id: str, filename: str) -> str:
    """Build GCS object path."""
    safe_name = _clean_filename(filename)
    prefix = settings.GCS_OBJECT_PREFIX.strip("/")
    if prefix:
        return f"{prefix}/{file_id}/{safe_name}"
    return f"{file_id}/{safe_name}"


async def upload_resume_to_gcs(file: UploadFile) -> ResumeUploadResponse:
    """
    Upload resume file to GCS and return session info.
    """
    _validate_filename(file.filename)

    if not settings.GCS_BUCKET_NAME:
        raise HTTPException(
            status_code=GCS_BUCKET_NOT_FOUND.code,
            detail=GCS_BUCKET_NOT_FOUND.detail,
        )

    file_id = str(uuid.uuid4())
    object_name = _build_object_name(file_id, file.filename)

    # Read file content into memory with size validation
    content = await _read_file_content(file)

    # Deep validation for PDF content (reject scanned copies)
    if Path(file.filename).suffix.lower() == ".pdf":
        await run_in_threadpool(_validate_pdf_content, content)

    try:
        # Run synchronous GCS upload in a thread pool
        await run_in_threadpool(
            _do_gcs_upload,
            content=content,
            object_name=object_name,
            content_type=file.content_type,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=GCS_UPLOAD_FAILED.code,
            detail=GCS_UPLOAD_FAILED.detail,
        ) from exc

    # Set expiration time based on configuration
    expire_at = (
        datetime.now(timezone.utc) + timedelta(hours=settings.SESSION_EXPIRY_HOURS)
    ).isoformat()

    return ResumeUploadResponse(
        code=201,
        status="ok",
        data=ResumeUploadData(
            session_id=file_id,
            expire_at=expire_at
        )
    )


async def _read_file_content(file: UploadFile) -> bytes:
    """Read file content with size limit check."""
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    size = 0
    chunks = []
    try:
        while True:
            chunk = await file.read(1024 * 1024)  # 1MB
            if not chunk:
                break
            size += len(chunk)
            if size > max_size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File too large. Max {settings.MAX_FILE_SIZE_MB}MB",
                )
            chunks.append(chunk)
    finally:
        await file.close()
    return b"".join(chunks)


def _do_gcs_upload(
    content: bytes, object_name: str, content_type: Optional[str]
) -> None:
    """Synchronous GCS upload operation with expiration metadata."""
    client = _get_gcs_client()
    bucket = client.bucket(settings.GCS_BUCKET_NAME)
    blob = bucket.blob(object_name)
    
    # Set expiration metadata
    expire_at = (
        datetime.now(timezone.utc) + timedelta(hours=settings.SESSION_EXPIRY_HOURS)
    ).isoformat()
    blob.metadata = {"expire_at": expire_at}
    
    blob.upload_from_string(
        content, content_type=content_type or "application/octet-stream"
    )


def _build_service_account_credentials() -> Optional[service_account.Credentials]:
    """Build service account credentials from environment variables if available."""

    raw_key = (settings.GCP_SA_KEY or "").strip()
    if raw_key:
        info = _parse_service_account_payload(raw_key)
        return service_account.Credentials.from_service_account_info(info)

    return None


def _parse_service_account_payload(raw: str) -> Dict[str, Any]:
    """Parse service account JSON or base64 payload, normalizing private key format."""

    payload = raw
    if not raw.startswith("{"):
        try:
            payload = base64.b64decode(raw).decode("utf-8")
        except Exception as exc:  # pragma: no cover - defensive
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Invalid service account payload: {exc}",
            ) from exc

    try:
        info = json.loads(payload)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid service account JSON: {exc}",
        ) from exc

    if "private_key" in info:
        info["private_key"] = info["private_key"].replace("\\n", "\n")

    if not info.get("project_id") and settings.GCP_PROJECT_ID:
        info["project_id"] = settings.GCP_PROJECT_ID

    return info


# ============================================================================
# RA-24: File Parsing Functions (Integrated from Incoming)
# ============================================================================


def _extract_structured_data(raw_text: str, filename: str) -> ResumeData:
    """
    Extract structured information from raw text using regex patterns (Bonus RA-24)
    """
    # Extract email
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    emails = re.findall(email_pattern, raw_text)
    email = emails[0] if emails else None

    # Extract phone
    phone_pattern = r"\b(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}\b"
    raw_phones = re.findall(phone_pattern, raw_text)
    phones = [p for p in raw_phones if 7 <= len(re.sub(r"\D", "", p)) <= 15]
    phone = phones[0] if phones else None

    # Extract LinkedIn
    linkedin_pattern = r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+"
    linkedin_urls = re.findall(linkedin_pattern, raw_text, re.IGNORECASE)
    linkedin = linkedin_urls[0] if linkedin_urls else None

    # Extract name (heuristic: first non-empty line)
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    full_name = lines[0] if lines else None

    contact_info = ContactInfo(
        email=email,
        phone=phone,
        linkedin=linkedin,
        location=None,
    )

    return ResumeData(
        full_name=full_name,
        contact_info=contact_info,
        summary=_extract_summary(raw_text),
        skills=_extract_skills(raw_text),
        education=_extract_education(raw_text),
        work_experience=_extract_work_experience(raw_text),
        raw_text=raw_text,
    )


def _extract_skills(text: str) -> list[str]:
    skills = []
    skills_pattern = r"(?:skills?|technical skills?|core competencies)[\s:]*\n((?:[^\n]+\n?)+?)(?:\n\n|experience|employment|work history|education|$)"
    match = re.search(skills_pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        skill_items = re.split(r"[,;•·\|]|\n", match.group(1))
        skills = [s.strip() for s in skill_items if s.strip() and len(s.strip()) > 2]
    return skills[:20]


def _extract_education(text: str) -> list[Education]:
    education_list = []
    edu_pattern = r"(?:education|academic background)[\s:]*\n((?:[^\n]+\n?)+?)(?:\n\n|experience|skills|$)"
    match = re.search(edu_pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        edu_text = match.group(1)
        current_entry = []
        for line in edu_text.split("\n"):
            line = line.strip()
            if not line:
                if current_entry:
                    education_list.append(_classify_education_fields(current_entry))
                    current_entry = []
                continue
            current_entry.append(line)
        if current_entry:
            education_list.append(_classify_education_fields(current_entry))
    return education_list[:5]


def _classify_education_fields(entry_lines: list[str]) -> Education:
    institution, degree, field = None, None, None
    for line in entry_lines:
        lower_line = line.lower()
        if institution is None and re.search(r"\b(university|college|institute|school)\b", lower_line):
            institution = line
        elif degree is None and re.search(r"\b(bachelor|master|ph\.?d|phd|b\.?sc|m\.?sc|ba|bs|beng|meng|mba)\b", lower_line):
            degree = line
        elif field is None:
            field = line
    if institution is None and len(entry_lines) > 0:
        institution = entry_lines[0]
    return Education(institution=institution, degree=degree, field=field)


def _extract_work_experience(text: str) -> list[WorkExperience]:
    experience_list = []
    exp_pattern = r"(?:experience|employment|work history)[\s:]*\n((?:[^\n]+\n?)+?)(?:\n\n|education|skills|$)"
    match = re.search(exp_pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        lines = [line.strip() for line in match.group(1).split("\n") if line.strip()]
        for i in range(0, len(lines), 3):
            if i + 2 < len(lines):
                experience_list.append(WorkExperience(company=lines[i], position=lines[i+1], duration=lines[i+2]))
    return experience_list[:10]


def _extract_summary(text: str) -> Optional[str]:
    summary_pattern = r"(?:summary|objective|profile|about)[\s:]*\n((?:[^\n]+\n?)+?)(?:\n\n|experience|employment|work history|education|skills|$)"
    match = re.search(summary_pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        summary = match.group(1).strip()
        return summary[:500] if len(summary) > 500 else summary
    return None
