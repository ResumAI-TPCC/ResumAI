"""
API Route Aggregation Module
"""

from fastapi import APIRouter

from .resumes import router as resumes_router
from .jobs import router as jobs_router

router = APIRouter()

# Register sub-routes
router.include_router(resumes_router, prefix="/resumes", tags=["Resume"])
router.include_router(jobs_router, prefix="/jobs", tags=["Jobs"])  # RA-82
