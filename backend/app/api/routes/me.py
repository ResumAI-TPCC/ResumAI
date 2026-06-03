"""
Current user API routes.
"""

from fastapi import APIRouter, Depends

from app.core.auth import get_current_user_claims
from app.schemas.auth_schema import CurrentUserClaims, MeResponse

router = APIRouter()


@router.get("/me", response_model=MeResponse)
async def get_me(
    current_user: CurrentUserClaims = Depends(get_current_user_claims),
) -> MeResponse:
    """Return the authenticated Firebase user recognized by the backend."""
    return MeResponse(data=current_user)
