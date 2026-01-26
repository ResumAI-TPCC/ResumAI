"""
API Route Aggregation Module
"""

from fastapi import APIRouter

from .resume import router as api_router

router = APIRouter()

# Register sub-routes
router.include_router(api_router, prefix="/resumes", tags=["Resume"])
