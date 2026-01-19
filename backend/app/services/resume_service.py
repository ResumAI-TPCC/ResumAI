"""
Resume Service Layer
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Dict, Optional

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


def _build_object_name(file_id: str, filename: str) -> str:
    safe_name = Path(filename).name
    prefix = settings.gcs_object_prefix.strip("/")
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

    if not settings.gcs_bucket_name:
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

    storage_path = f"gs://{settings.gcs_bucket_name}/{object_name}"
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
    bucket = client.bucket(settings.gcs_bucket_name)
    blob = bucket.blob(object_name)
    blob.upload_from_string(
        content, content_type=content_type or "application/octet-stream"
    )
