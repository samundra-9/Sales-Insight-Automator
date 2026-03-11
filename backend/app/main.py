import os
import uvicorn
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from app.api.endpoints import router
from app.security.api_key_auth import get_api_key
from app.utils.logger import setup_logging

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application startup")
    yield
    # Shutdown
    logger.info("Application shutdown")


app = FastAPI(
    title="Sales Insight Automator API",
    description="API for uploading sales data, generating AI summaries, and sending email reports.",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Configuration
origins = [
    "http://localhost:3000",
    "https://sales-insight-automa-git-610dd7-samundra1614be23-3558s-projects.vercel.app",
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


@app.get("/", tags=["System"])
async def root():
    return {"status": "Sales Insight Automator API running"}


@app.get("/health", tags=["System"], summary="Health check endpoint")
async def health_check():
    logger.info("Health check requested.")
    return JSONResponse(
        content={"status": "ok", "message": "Sales Insight Automator is running!"}
    )


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        logger.warning(f"Unauthorized access attempt: {request.url}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid API Key"},
        )

    if exc.status_code == status.HTTP_403_FORBIDDEN:
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
