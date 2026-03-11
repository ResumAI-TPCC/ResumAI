"""
Google Cloud Storage Service

Handles all GCS operations including upload, download, and credential management.
Provides clean separation of storage concerns from business logic.
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from google.cloud import storage
from google.oauth2 import service_account

from app.core.config import settings
from app.core.error_templates import (
    GCS_BUCKET_NOT_FOUND,
    GCS_UPLOAD_FAILED,
)


def get_gcs_client() -> storage.Client:
    """
    Create a new GCS client instance for each operation.
    
    The Google Cloud Storage SDK handles connection pooling internally,
    so creating new client instances per operation is efficient and avoids
    global state management issues.
    
    Returns:
        storage.Client: New GCS client instance
    """
    credentials = build_service_account_credentials()

    # Use Application Default Credentials (ADC) if no explicit credentials provided
    if credentials is not None:
        return storage.Client(
            project=settings.GCP_PROJECT_ID or None, credentials=credentials
        )
    else:
        return storage.Client(project=settings.GCP_PROJECT_ID or None)


def upload_file_to_gcs(
    content: bytes,
    object_name: str,
    content_type: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None,
) -> None:
    """
    Upload file content to GCS with metadata.
    
    Args:
        content: File content as bytes
        object_name: GCS object path (e.g., "resumes/session-id/file.pdf")
        content_type: MIME type (defaults to "application/octet-stream")
        metadata: Optional metadata dict (auto-adds expiration if not provided)
        
    Raises:
        HTTPException: If upload fails or bucket not found
    """
    try:
        client = get_gcs_client()
        bucket = client.bucket(settings.GCS_BUCKET_NAME)
        
        # Check if bucket exists
        if not bucket.exists():
            raise HTTPException(
                status_code=GCS_BUCKET_NOT_FOUND.code,
                detail=GCS_BUCKET_NOT_FOUND.detail,
            )
        
        blob = bucket.blob(object_name)
        
        # Set expiration metadata if not provided
        if metadata is None:
            expire_at = (
                datetime.now(timezone.utc) + timedelta(hours=settings.SESSION_EXPIRY_HOURS)
            ).isoformat()
            metadata = {"expire_at": expire_at}
        
        blob.metadata = metadata
        blob.upload_from_string(
            content, content_type=content_type or "application/octet-stream"
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=GCS_UPLOAD_FAILED.code,
            detail=GCS_UPLOAD_FAILED.detail,
        ) from exc


def download_file_from_gcs(session_id: str, filename: str) -> bytes:
    """
    Download file content from GCS.
    
    Args:
        session_id: Session identifier
        filename: Original filename
        
    Returns:
        bytes: File content
        
    Raises:
        HTTPException: If file not found or download fails
    """
    client = get_gcs_client()
    bucket = client.bucket(settings.GCS_BUCKET_NAME)
    
    prefix = settings.GCS_OBJECT_PREFIX or "resumes"
    object_name = f"{prefix}/{session_id}/{filename}"
    
    blob = bucket.blob(object_name)
    
    if not blob.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found in storage",
        )
    
    return blob.download_as_bytes()


def build_service_account_credentials() -> Optional[service_account.Credentials]:
    """
    Build service account credentials from environment variables if available.
    
    Returns:
        Service account credentials or None (falls back to ADC)
        
    Note:
        If GCP_SA_KEY is not set, returns None and GCS client will use
        Application Default Credentials (ADC).
    """
    raw_key = (settings.GCP_SA_KEY or "").strip()
    if not raw_key:
        return None
    
    info = _parse_service_account_payload(raw_key)
    return service_account.Credentials.from_service_account_info(info)


def _parse_service_account_payload(raw: str) -> Dict[str, Any]:
    """
    Parse service account JSON or base64 payload, normalizing private key format.
    
    Args:
        raw: Service account JSON string or base64-encoded JSON
        
    Returns:
        Dict containing service account info
        
    Raises:
        HTTPException: If payload is invalid
    """
    payload = raw
    
    # Decode base64 if not JSON
    if not raw.startswith("{"):
        try:
            payload = base64.b64decode(raw).decode("utf-8")
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Invalid service account payload: {exc}",
            ) from exc
    
    # Parse JSON
    try:
        info = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid service account JSON: {exc}",
        ) from exc
    
    # Normalize private key newlines
    if "private_key" in info:
        info["private_key"] = info["private_key"].replace("\\n", "\n")
    
    # Add project_id if missing
    if not info.get("project_id") and settings.GCP_PROJECT_ID:
        info["project_id"] = settings.GCP_PROJECT_ID
    
    return info
