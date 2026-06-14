"""
API Route Aggregation Module
"""

from fastapi import APIRouter

from .interviews import router as interview_router
from .resumes import router as api_router

router = APIRouter()

# Register sub-routes
router.include_router(api_router, prefix="/resumes", tags=["Resume"])
router.include_router(interview_router, prefix="/interviews", tags=["Interview"])
