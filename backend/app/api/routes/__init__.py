"""
API Route Aggregation Module
"""

from fastapi import APIRouter, Depends

from app.core.auth import get_current_user_claims

from .me import router as me_router
from .resumes import router as api_router
from .resumes_v1 import router as api_router_v1

router = APIRouter()

# Register sub-routes
router.include_router(me_router, tags=["Auth"])
router.include_router(
    api_router,
    prefix="/resumes",
    tags=["Resume"],
    dependencies=[Depends(get_current_user_claims)],
)
router.include_router(
    api_router_v1,
    prefix="/v1/resumes",
    tags=["Resume V1"],
    dependencies=[Depends(get_current_user_claims)],
)
