"""
Session Validator Service

Validates session IDs and expiration times for security and data integrity.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from fastapi import HTTPException
from google.cloud import storage

from app.core.error_templates import INVALID_SESSION_ID, SESSION_EXPIRED

# UUID validation pattern (RFC 4122 compliant)
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)


def validate_session_id(session_id: str) -> None:
    """
    Validate session ID is a proper UUID format to prevent path traversal attacks.
    
    Args:
        session_id: Session ID to validate
        
    Raises:
        HTTPException(400): If session_id is not a valid UUID format
        
    Example:
        >>> validate_session_id("7c9e6679-7425-40de-944b-e07fc1f90ae7")  # OK
        >>> validate_session_id("../../../etc/passwd")  # Raises HTTPException
    """
    if not session_id or not UUID_PATTERN.match(session_id):
        raise HTTPException(
            status_code=INVALID_SESSION_ID.code,
            detail=INVALID_SESSION_ID.detail,
        )


def validate_session_expiry(blob: storage.Blob) -> None:
    """
    Validate that the session has not expired based on blob metadata.
    
    Args:
        blob: GCS blob containing the resume file
        
    Raises:
        HTTPException(404): If session has expired
        
    Note:
        If no expiration metadata exists, the session is considered valid.
        This allows backward compatibility with files uploaded before
        expiration tracking was implemented.
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
    except ValueError:
        # Invalid date format in metadata, log but allow access
        # (Don't break functionality due to metadata issues)
        pass
