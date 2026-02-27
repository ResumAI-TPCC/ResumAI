"""
Resume Service Layer - Orchestration

Main service for resume operations. Coordinates between storage, parsers, and validators.
Provides high-level business logic for resume upload and content retrieval.

RA-23: Upload resume to GCS and return session info
RA-24: Parse resume file and extract text content

Note: Structured data extraction (_extract_structured_data, etc.) has been
      deferred to a future phase and removed to maintain focus on MVP.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.error_templates import (
    GCS_BUCKET_NOT_FOUND,
    SESSION_NOT_FOUND,
)
from app.schemas.resume_schema import (
    ResumeUploadData,
    ResumeUploadResponse,
)
from app.services.storage.gcs_service import get_gcs_client, upload_file_to_gcs
from app.services.parsers.document_parser import (
    parse_pdf_to_markdown,
    parse_docx_to_markdown,
    parse_doc_to_text,
    parse_txt_to_text,
)
from app.services.validators.session_validator import validate_session_id
from app.services.validators.file_validator import (
    validate_filename,
    validate_pdf_content,
    clean_filename,
)


# ============================================================================
# Public Service Functions
# ============================================================================


async def upload_resume_to_gcs(file: UploadFile) -> ResumeUploadResponse:
    """
    Upload resume file to GCS and return session information.
    
    Orchestrates file validation, upload to cloud storage, and session creation.
    
    Args:
        file: Uploaded file from FastAPI request
        
    Returns:
        ResumeUploadResponse: Session ID and expiration time
        
    Raises:
        HTTPException: If validation fails or upload errors occur
        
    Flow:
        1. Validate filename and extension
        2. Generate unique session ID (UUID)
        3. Read and validate file content
        4. For PDFs: Check for extractable text (reject scanned PDFs)
        5. Upload to GCS with metadata
        6. Return session info with expiration time
    """
    # 1. Validate filename
    validate_filename(file.filename)

    if not settings.GCS_BUCKET_NAME:
        raise HTTPException(
            status_code=GCS_BUCKET_NOT_FOUND.code,
            detail=GCS_BUCKET_NOT_FOUND.detail,
        )

    # 2. Generate session ID
    session_id = str(uuid.uuid4())
    
    # 3. Build GCS object path
    safe_name = clean_filename(file.filename)
    prefix = settings.GCS_OBJECT_PREFIX.strip("/")
    object_name = f"{prefix}/{session_id}/{safe_name}" if prefix else f"{session_id}/{safe_name}"

    # 4. Read file content with size validation
    content = await _read_file_content(file)

    # 5. Deep validation for PDF content (reject scanned copies)
    if Path(file.filename).suffix.lower() == ".pdf":
        await run_in_threadpool(validate_pdf_content, content)

    # 6. Upload to GCS
    await run_in_threadpool(
        upload_file_to_gcs,
        content=content,
        object_name=object_name,
        content_type=file.content_type,
    )

    # 7. Calculate expiration time
    expire_at = (
        datetime.now(timezone.utc) + timedelta(hours=settings.SESSION_EXPIRY_HOURS)
    ).isoformat()

    return ResumeUploadResponse(
        code=201,
        status="ok",
        data=ResumeUploadData(
            session_id=session_id,
            expire_at=expire_at
        )
    )


async def get_resume_content(session_id: str) -> str:
    """
    Retrieve resume file from GCS by session_id and return extracted text.
    
    Orchestrates session validation, file retrieval, and content parsing.
    
    Args:
        session_id: UUID session identifier
        
    Returns:
        str: Extracted text content from resume (markdown for DOCX, plain text for others)
        
    Raises:
        HTTPException(400): Invalid session ID format
        HTTPException(404): Session expired or not found
        HTTPException(422): Unsupported file type or parsing error
        
    Flow:
        1. Validate session ID format (prevent path traversal)
        2. List files in session directory
        3. Validate session expiration
        4. Download file content
        5. Parse based on extension (PDF→text, DOCX→markdown, etc.)
    """
    # 1. Validate session ID format to prevent path traversal
    validate_session_id(session_id)
    
    # 2. Connect to GCS and find session files
    client = get_gcs_client()
    bucket = client.bucket(settings.GCS_BUCKET_NAME)
    
    prefix = f"{settings.GCS_OBJECT_PREFIX.strip('/')}/{session_id}/"
    blobs = list(client.list_blobs(bucket, prefix=prefix))
    
    if not blobs:
        raise HTTPException(
            status_code=SESSION_NOT_FOUND.code,
            detail=SESSION_NOT_FOUND.detail,
        )
    
    # 3. Take the first file in the session directory
    target_blob = blobs[0]
    
    # Note: Session expiry validation currently commented out in original code
    # validate_session_expiry(target_blob)
    
    # 4. Download file content
    filename = target_blob.name
    content_bytes = await run_in_threadpool(target_blob.download_as_bytes)
    
    # 5. Parse content based on file extension
    ext = Path(filename).suffix.lower()
    
    if ext == ".pdf":
        return await run_in_threadpool(parse_pdf_to_markdown, content_bytes)
    elif ext == ".docx":
        return await run_in_threadpool(parse_docx_to_markdown, content_bytes)
    elif ext == ".doc":
        return await run_in_threadpool(parse_doc_to_text, content_bytes)
    elif ext == ".txt":
        return await run_in_threadpool(parse_txt_to_text, content_bytes)
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type in storage: {ext}",
        )


# ============================================================================
# Private Helper Functions
# ============================================================================


async def _read_file_content(file: UploadFile) -> bytes:
    """
    Read file content with size limit validation.
    
    Args:
        file: Uploaded file from FastAPI request
        
    Returns:
        bytes: File content
        
    Raises:
        HTTPException(400): If file exceeds size limit
    """
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    size = 0
    chunks = []
    
    try:
        while True:
            chunk = await file.read(1024 * 1024)  # Read 1MB at a time
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
