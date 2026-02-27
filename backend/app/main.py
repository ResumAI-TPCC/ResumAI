"""
ResumAI Backend Application Entry Point
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    print(f"{settings.APP_NAME} v{settings.APP_VERSION} starting...")
    yield
    # Shutdown
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
