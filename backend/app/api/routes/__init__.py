"""
API Route Aggregation Module
"""

from fastapi import APIRouter

from .resume import router as api_router

router = APIRouter()

# Register sub-routes
# TODO: Route prefix and tags will be updated by RA-12
router.include_router(api_router, prefix="/resume", tags=["Resume"])
