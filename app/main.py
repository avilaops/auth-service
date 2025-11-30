"""Main FastAPI application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from prometheus_client import make_asgi_app
from .config import settings
from .database import (
    connect_to_mongo, close_mongo_connection,
    connect_to_redis, close_redis_connection
)
from .routes import auth, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan"""
    # Startup
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await connect_to_mongo()
    await connect_to_redis()
    print("✅ All services connected")

    yield

    # Shutdown
    print("🛑 Shutting down...")
    await close_mongo_connection()
    await close_redis_connection()
    print("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="🔐 Centralized authentication service for Ávila Inc platform",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router)
app.include_router(users.router)

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
        "metrics": "/metrics"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    from .database import get_database, get_redis

    # Check MongoDB
    try:
        db = get_database()
        await db.command("ping")
        mongo_status = "healthy"
    except:
        mongo_status = "unhealthy"

    # Check Redis
    try:
        redis_client = get_redis()
        await redis_client.ping()
        redis_status = "healthy"
    except:
        redis_status = "unhealthy"

    overall_status = "healthy" if mongo_status == "healthy" and redis_status == "healthy" else "degraded"

    return {
        "status": overall_status,
        "services": {
            "mongodb": mongo_status,
            "redis": redis_status
        }
    }
