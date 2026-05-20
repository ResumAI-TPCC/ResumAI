"""
API Route Aggregation Module
"""

from fastapi import APIRouter

from .resumes import router as api_router
from .resumes_v1 import router as api_router_v1

router = APIRouter()

# Register sub-routes
router.include_router(api_router, prefix="/resumes", tags=["Resume"])
router.include_router(api_router_v1, prefix="/v1/resumes", tags=["Resume V1"])