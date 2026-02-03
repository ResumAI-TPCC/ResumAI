"""
Resume Service Layer
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

ALLOWED_EXTS = {".pdf", ".docx"}
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10MB

# Global GCS client instance for reuse
_gcs_client: Optional[storage.Client] = None


def _get_gcs_client() -> storage.Client:
    """Get or create a GCS client instance."""
    global _gcs_client
    if _gcs_client is not None:
        return _gcs_client

    credentials = _build_service_account_credentials()

    # Use Application Default Credentials (ADC) if no explicit credentials provided
    if credentials is not None:
        _gcs_client = storage.Client(
            project=settings.gcp_project_id or None, credentials=credentials
        )
    else:
        _gcs_client = storage.Client(project=settings.gcp_project_id or None)
    return _gcs_client


def _validate_filename(filename: str) -> None:
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
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scanned PDFs are not supported. Please upload a text-based PDF.",
            )
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or corrupted PDF file: {exc}",
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
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No extractable text found in PDF. Scanned PDFs are not supported.",
            )
        return result
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse PDF content: {exc}",
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
                # (Simplification: if the whole paragraph is bold or has bold runs)
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
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No text found in DOCX file.",
            )
        return result
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse DOCX content: {exc}",
        ) from exc


async def get_resume_content(session_id: str) -> str:
    """
    Download and parse resume content from GCS.
    
    Args:
        session_id: The unique session/file identifier
        
    Returns:
        str: Parsed resume content (Plain Text for PDF, Markdown for DOCX)
        
    Raises:
        HTTPException: If file not found or parsing fails
    """
    client = _get_gcs_client()
    bucket = client.bucket(settings.gcs_bucket_name)
    
    # List blobs with the session prefix to find the file
    prefix = f"{settings.gcs_object_prefix.strip('/')}/{session_id}/"
    blobs = list(client.list_blobs(bucket, prefix=prefix))
    
    if not blobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No resume file found for session: {session_id}",
        )
    
    # Strategy: Take the first found file in the session directory
    target_blob = blobs[0]
    filename = target_blob.name
    content_bytes = await run_in_threadpool(target_blob.download_as_bytes)
    
    # Branching based on file extension
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return await run_in_threadpool(_parse_pdf_to_text, content_bytes)
    elif ext == ".docx":
        return await run_in_threadpool(_parse_docx_to_markdown, content_bytes)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type in storage: {ext}",
        )


def _build_object_name(file_id: str, filename: str) -> str:
    safe_name = _clean_filename(filename)
    prefix = settings.gcs_object_prefix.strip("/")
    if prefix:
        return f"{prefix}/{file_id}/{safe_name}"
    return f"{file_id}/{safe_name}"


async def upload_resume_to_gcs(file: UploadFile) -> Dict[str, Any]:
    """
    Upload resume file to GCS.
    Returns:
        dict: {code, status, data: {session_id, expire_at}}
    """
    _validate_filename(file.filename)

    if not settings.gcs_bucket_name:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GCS bucket not configured",
        )

    file_id = str(uuid.uuid4())
    object_name = _build_object_name(file_id, file.filename)

    # Read file content into memory with size validation
    content = await _read_file_content(file)

    # Deep validation for PDF content (reject scanned copies)
    if Path(file.filename).suffix.lower() == ".pdf":
        await run_in_threadpool(_validate_pdf_content, content)

    try:
        # Run synchronous GCS upload in a thread pool to avoid blocking the event loop
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

    # Set expiration to 24 hours from now
    expire_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()

    return {
        "code": 201,
        "status": "ok",
        "data": {
            "session_id": file_id,
            "expire_at": expire_at
        }
    }


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
                    detail=f"File too large. Max {MAX_SIZE_BYTES} bytes",
                )
            chunks.append(chunk)
    finally:
        await file.close()
    return b"".join(chunks)


def _do_gcs_upload(
    content: bytes, object_name: str, content_type: Optional[str]
) -> None:
    """Synchronous GCS upload operation."""
    client = _get_gcs_client()
    bucket = client.bucket(settings.gcs_bucket_name)
    blob = bucket.blob(object_name)
    blob.upload_from_string(
        content, content_type=content_type or "application/octet-stream"
    )


def _build_service_account_credentials() -> Optional[service_account.Credentials]:
    """Build service account credentials from environment variables if available."""

    raw_key = (settings.gcp_sa_key or "").strip()
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

    if not info.get("project_id") and settings.gcp_project_id:
        info["project_id"] = settings.gcp_project_id

    return info
