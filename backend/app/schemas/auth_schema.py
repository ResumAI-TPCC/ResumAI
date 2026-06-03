"""
Authentication schemas
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class CurrentUserClaims(BaseModel):
    """Normalized Firebase user claims used inside the API."""

    firebase_uid: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    email_verified: bool = False
    claims: Dict[str, Any] = Field(default_factory=dict)


class MeResponse(BaseModel):
    """Response schema for GET /api/me."""

    code: int = 200
    status: str = "ok"
    data: CurrentUserClaims
