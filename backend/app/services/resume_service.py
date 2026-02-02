"""
Resume Service Layer
"""

from __future__ import annotations

import io
import uuid
from pathlib import Path
from typing import Dict, Optional, Tuple

from fastapi import HTTPException, UploadFile, status
from google.cloud import storage
from starlette.concurrency import run_in_threadpool

from app.core.config import settings

ALLOWED_EXTS = {".pdf", ".doc", ".docx", ".txt"}
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10MB

# Global GCS client instance for reuse
_gcs_client: Optional[storage.Client] = None


def _get_gcs_client() -> storage.Client:
    """Get or create a GCS client instance."""
    global _gcs_client
    if _gcs_client is not None:
        return _gcs_client

    # Use Application Default Credentials (ADC)
    _gcs_client = storage.Client(project=settings.GCP_PROJECT_ID or None)
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


def _build_object_name(file_id: str, filename: str) -> str:
    safe_name = Path(filename).name
    prefix = settings.GCS_OBJECT_PREFIX.strip("/")
    if prefix:
        return f"{prefix}/{file_id}/{safe_name}"
    return f"{file_id}/{safe_name}"


async def upload_resume_to_gcs(file: UploadFile) -> Dict[str, str]:
    """
    Upload resume file to GCS.
    Returns:
        dict: {file_id, filename, storage_path}
    """
    _validate_filename(file.filename)

    if not settings.GCS_BUCKET_NAME:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GCS bucket not configured",
        )

    file_id = str(uuid.uuid4())
    object_name = _build_object_name(file_id, file.filename)

    # Read file content into memory with size validation
    content = await _read_file_content(file)

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

    storage_path = f"gs://{settings.GCS_BUCKET_NAME}/{object_name}"
    return {"file_id": file_id, "filename": file.filename, "storage_path": storage_path}


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
    bucket = client.bucket(settings.GCS_BUCKET_NAME)
    blob = bucket.blob(object_name)
    blob.upload_from_string(
        content, content_type=content_type or "application/octet-stream"
    )


# ============================================================================
# GCS Download and Resume Parsing Functions
# ============================================================================


async def get_resume_from_gcs(session_id: str) -> Tuple[bytes, str]:
    """
    Download resume file from GCS by session_id.

    Args:
        session_id: The file_id/session_id returned from upload

    Returns:
        Tuple[bytes, str]: (file_content, filename)

    Raises:
        HTTPException: 404 if resume not found, 500 if download fails
    """
    if not settings.GCS_BUCKET_NAME:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GCS bucket not configured",
        )

    try:
        content, filename = await run_in_threadpool(
            _do_gcs_download, session_id=session_id
        )
        return content, filename
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download resume from GCS: {exc}",
        ) from exc


def _do_gcs_download(session_id: str) -> Tuple[bytes, str]:
    """
    Synchronous GCS download operation.

    Args:
        session_id: The file_id/session_id

    Returns:
        Tuple[bytes, str]: (file_content, filename)
    """
    client = _get_gcs_client()
    bucket = client.bucket(settings.GCS_BUCKET_NAME)

    # List blobs with the session_id prefix
    prefix = f"{settings.GCS_OBJECT_PREFIX}/{session_id}/"
    blobs = list(bucket.list_blobs(prefix=prefix))

    if not blobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume not found for session: {session_id}",
        )

    # Get the first (and should be only) file
    blob = blobs[0]
    content = blob.download_as_bytes()

    # Extract filename from blob name
    filename = Path(blob.name).name

    return content, filename


def parse_resume_content(content: bytes, filename: str) -> str:
    """
    Parse resume file and extract text content.

    Supports PDF, DOCX, DOC, and TXT formats.

    Args:
        content: File content as bytes
        filename: Original filename (to determine file type)

    Returns:
        str: Extracted text content

    Raises:
        HTTPException: 400 if file type is unsupported or parsing fails
    """
    ext = Path(filename).suffix.lower()

    try:
        if ext == ".txt":
            return content.decode("utf-8")

        elif ext == ".pdf":
            return _parse_pdf(content)

        elif ext in (".docx", ".doc"):
            return _parse_docx(content)

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type for parsing: {ext}",
            )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse resume file: {exc}",
        ) from exc


def _parse_pdf(content: bytes) -> str:
    """
    Parse PDF file and extract text.

    Args:
        content: PDF file content as bytes

    Returns:
        str: Extracted text content
    """
    import pdfplumber

    text_parts = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    if not text_parts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract text from PDF. The file may be empty or image-based.",
        )

    return "\n\n".join(text_parts)


def _parse_docx(content: bytes) -> str:
    """
    Parse DOCX file and extract text.

    Args:
        content: DOCX file content as bytes

    Returns:
        str: Extracted text content
    """
    from docx import Document

    doc = Document(io.BytesIO(content))
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]

    if not paragraphs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract text from DOCX. The file may be empty.",
        )

    return "\n\n".join(paragraphs)


async def get_resume_text(session_id: str) -> str:
    """
    Get resume text content by session_id.

    This is a high-level function that:
    1. Downloads the resume file from GCS
    2. Parses the file to extract text content

    Args:
        session_id: The file_id/session_id returned from upload

    Returns:
        str: Extracted text content from the resume

    Raises:
        HTTPException: 404 if not found, 400 if parsing fails, 500 if other error
    """
    # Download from GCS
    content, filename = await get_resume_from_gcs(session_id)

    # Parse and extract text (run in thread pool for CPU-bound parsing)
    text = await run_in_threadpool(parse_resume_content, content, filename)

    return text
