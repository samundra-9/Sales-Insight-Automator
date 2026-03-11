
import os
import uvicorn
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from redis import asyncio as aioredis

from app.api.endpoints import router
from app.security.api_key_auth import get_api_key
from app.utils.logger import setup_logging
from app.security.rate_limiter import init_rate_limiter, close_rate_limiter

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application startup")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    app.state.redis = aioredis.from_url(REDIS_URL)
    try:
        await app.state.redis.ping()
        logger.info("Connected to Redis")
        init_rate_limiter(REDIS_URL) # Initialize rate limiter with Redis
    except Exception as e:
        logger.error(f"Could not connect to Redis: {e}")
        # Depending on criticality, you might want to raise an exception here
        # to prevent the app from starting without Redis.
    yield
    # Shutdown
    logger.info("Application shutdown")
    if hasattr(app.state, 'redis') and app.state.redis:
        await app.state.redis.close()
        logger.info("Disconnected from Redis")
    await close_rate_limiter() # Close rate limiter Redis connection

app = FastAPI(
    title="Sales Insight Automator API",
    description="API for uploading sales data, generating AI summaries, and sending email reports.",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
origins = [
    os.getenv("FRONTEND_URL", "http://localhost:3000"),  # Frontend URL
    # Add other origins as needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(router, dependencies=[Depends(get_api_key)])

@app.get("/health", tags=["System"], summary="Health check endpoint")
async def health_check():
    logger.info("Health check requested.")
    return JSONResponse(content={"status": "ok", "message": "Sales Insight Automator is running!"})


# Global exception handler for API key authentication errors
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        logger.warning(f"Unauthorized access attempt: {request.url}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid API Key"},
        )
    elif exc.status_code == status.HTTP_403_FORBIDDEN:
        logger.warning(f"Forbidden access attempt: {request.url}")
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Rate limit exceeded"},
        )
    logger.error(f"Unhandled HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


logger.info("FastAPI application initialized.")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)