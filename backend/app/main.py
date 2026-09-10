"""
FastAPI application entry point.

This is where everything comes together:
- The FastAPI app instance is created
- CORS middleware is configured
- API routers are mounted
- The health endpoint lives here (it's infrastructure, not a feature)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import v1_router
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Code before `yield` runs on startup.
    Code after `yield` runs on shutdown.

    We'll use this later for:
    - Creating database connection pools
    - Loading ML models
    - Initializing caches
    """
    # --- Startup ---
    print(f"🚀 Starting {settings.APP_NAME}")
    print(f"📋 Debug mode: {settings.DEBUG}")
    yield
    # --- Shutdown ---
    print(f"👋 Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered placement intelligence platform for college students.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc
)

# --- CORS ---
# Allow all origins in development. Lock this down in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Mount API Routers ---
app.include_router(v1_router, prefix=settings.API_V1_PREFIX)


# --- Health Check ---
@app.get(
    "/health",
    tags=["Infrastructure"],
    summary="Health check",
    response_description="Returns service health status",
)
async def health_check():
    """
    Basic health check endpoint.

    Used by load balancers, monitoring systems, and deployment checks
    to verify the service is alive and responding.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "0.1.0",
    }
