"""
API Route Aggregation Module
"""

from fastapi import APIRouter

from .chat import router as chat_router

router = APIRouter()

# Register sub-routes
router.include_router(chat_router, prefix="/chat", tags=["Chat"])

