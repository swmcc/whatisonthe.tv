"""Main FastAPI application."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api import auth, checkin, search, swanson
from app.core.config import settings
from app.db.redis import close_redis, get_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    await get_redis()
    print("✅ Redis connected")

    yield

    # Shutdown
    await close_redis()
    print("👋 Redis connection closed")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router)
app.include_router(search.router, tags=["search"])
app.include_router(checkin.router)
app.include_router(swanson.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Serve frontend static files (for Heroku deployment)
# Check if frontend build directory exists
frontend_build_path = Path(__file__).parent.parent.parent / "frontend" / "build"
if frontend_build_path.exists():
    # Mount static files from SvelteKit build
    app.mount("/_app", StaticFiles(directory=str(frontend_build_path / "_app")), name="app")

    # Catch-all route to serve index.html for SPA routing
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve frontend for all non-API routes."""
        # Don't intercept API routes
        if full_path.startswith(("api/", "health", "docs", "redoc", "openapi.json")):
            return {"error": "Not found"}

        # Try to serve static file first
        file_path = frontend_build_path / full_path
        if file_path.is_file():
            return FileResponse(file_path)

        # Fall back to index.html for SPA routing
        index_path = frontend_build_path / "index.html"
        if index_path.exists():
            return FileResponse(index_path)

        return {"error": "Frontend not built"}
else:
    # Development mode - just show API status
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "app": settings.app_name,
            "version": settings.version,
            "status": "running",
            "note": "Frontend not built. Run: cd frontend && npm run build"
        }
