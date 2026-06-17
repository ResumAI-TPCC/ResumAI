"""
ResumAI Backend Application Entry Point
"""

import sys
from pathlib import Path

# Ensure repo root is in sys.path so `worker.*` can be imported
# when uvicorn loads this module directly (e.g. in production / Docker).
_repo_root = Path(__file__).resolve().parent.parent.parent  # ResumAI/
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.core.config import settings
from app.services.jobs.store import InMemoryJobStore
from app.services.jobs.manager import JobManager
from worker.runners.local_runner import LocalBackgroundRunner


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup: initialise job infrastructure
    store = InMemoryJobStore()
    runner = LocalBackgroundRunner()
    runner.set_store(store)
    app.state.job_manager = JobManager(store=store, runner=runner)

    print(f"{settings.APP_NAME} v{settings.APP_VERSION} starting...")
    yield
    # Shutdown
    runner.shutdown()
    print(f"{settings.APP_NAME} shutting down...")


def create_app() -> FastAPI:
    """Create FastAPI application instance"""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="ResumAI - AI-powered Resume Optimization Assistant",
        docs_url=f"{settings.API_PREFIX}/docs",
        redoc_url=f"{settings.API_PREFIX}/redoc",
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        lifespan=lifespan,
    )
 
    # Configure CORS middleware
    allowed_origins = [
        origin.strip() 
        for origin in settings.ALLOWED_ORIGINS.split(",") 
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(api_router, prefix=settings.API_PREFIX)

    return app


app = create_app()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
