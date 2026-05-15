"""
Jarvis AI - Main FastAPI Application
Production-ready async web server with proper error handling
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logger import setup_logging, get_logger
from app.core.brain import JarvisBrain

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Initialize brain (singleton)
brain: JarvisBrain = None


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ProcessRequest(BaseModel):
    """
    User request model for /process endpoint
    """

    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="User message or prompt",
    )
    use_cache: bool = Field(
        default=True,
        description="Whether to use cached responses",
    )

    class Config:
        """Pydantic config"""
        json_schema_extra = {
            "example": {
                "message": "Hello, how are you?",
                "use_cache": True,
            }
        }


class ProcessResponse(BaseModel):
    """
    Response model from /process endpoint
    """

    success: bool
    response: str | None = None
    thinking_time_ms: int = 0
    model_used: str | None = None
    cached: bool = False
    error: Dict[str, Any] | None = None

    class Config:
        """Pydantic config"""
        json_schema_extra = {
            "example": {
                "success": True,
                "response": "Hello! I'm Jarvis, your AI assistant.",
                "thinking_time_ms": 1250,
                "model_used": "gemini",
                "cached": False,
                "error": None,
            }
        }


class HealthResponse(BaseModel):
    """
    Health check response
    """

    status: str
    brain_status: str | None = None
    llm_provider: str | None = None
    environment: str
    version: str


# ============================================================================
# LIFESPAN EVENTS
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown
    """
    # Startup
    global brain
    try:
        logger.info("🚀 Starting Jarvis AI...")
        brain = JarvisBrain()
        logger.info("✅ Jarvis AI started successfully")
    except Exception as e:
        logger.error(f"❌ Failed to start Jarvis AI: {str(e)}", exc_info=True)
        raise

    yield

    # Shutdown
    try:
        logger.info("🛑 Shutting down Jarvis AI...")
        if brain and brain.cache:
            brain.cache.clear()
        logger.info("✅ Jarvis AI shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}", exc_info=True)


# ============================================================================
# CREATE FASTAPI APP
# ============================================================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="JARVIS - Advanced AI Assistant Backend",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Handle HTTP exceptions
    """
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "type": "http_error",
                "message": exc.detail,
                "status_code": exc.status_code,
            },
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    Handle unexpected exceptions
    Prevents server crashes with structured error responses
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "type": "system_error",
                "message": "Internal server error. Please try again later.",
                "status_code": 500,
            },
        },
    )


# ============================================================================
# API ENDPOINTS
# ============================================================================


@app.get("/")
async def root() -> Dict[str, Any]:
    """
    Root endpoint - API information
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/api/docs",
    }


@app.get("/health")
async def health_check() -> HealthResponse:
    """
    Health check endpoint
    Returns system status and configuration
    """
    try:
        brain_health = await brain.health_check() if brain else {"status": "not_initialized"}

        return HealthResponse(
            status="healthy" if brain_health.get("status") == "healthy" else "degraded",
            brain_status=brain_health.get("status"),
            llm_provider=brain_health.get("llm_provider"),
            environment=settings.ENVIRONMENT,
            version=settings.APP_VERSION,
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return HealthResponse(
            status="error",
            brain_status="error",
            environment=settings.ENVIRONMENT,
            version=settings.APP_VERSION,
        )


@app.post("/process", response_model=ProcessResponse)
async def process_message(request: ProcessRequest) -> ProcessResponse:
    """
    Main processing endpoint
    Sends user message to Jarvis brain and returns response

    Args:
        request: ProcessRequest with message and cache preference

    Returns:
        ProcessResponse with AI response and metadata
    """

    # Validate brain initialization
    if not brain:
        logger.error("Brain not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Brain not initialized",
        )

    try:
        logger.info(f"Processing message: {request.message[:100]}...")

        # Call brain with async support
        result = await brain.process(
            prompt=request.message,
            use_cache=request.use_cache,
        )

        # Ensure response is JSON-safe
        if not isinstance(result, dict):
            logger.error(f"Invalid response type: {type(result)}")
            return ProcessResponse(
                success=False,
                response=None,
                error={
                    "type": "invalid_response",
                    "message": "Invalid response from brain",
                },
            )

        # Extract and validate response fields
        return ProcessResponse(
            success=result.get("success", False),
            response=str(result.get("response")) if result.get("response") else None,
            thinking_time_ms=int(result.get("thinking_time_ms", 0)),
            model_used=str(result.get("model_used")) if result.get("model_used") else None,
            cached=bool(result.get("cached", False)),
            error=result.get("error"),
        )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message",
        )


@app.post("/chat")
async def chat(request: ProcessRequest) -> Dict[str, Any]:
    """
    Alias for /process endpoint
    Provides familiar 'chat' endpoint
    """
    return await process_message(request)


# ============================================================================
# STARTUP & DEBUG INFO
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on {settings.SERVER_HOST}:{settings.SERVER_PORT}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug: {settings.DEBUG}")
    logger.info(f"Log Level: {settings.LOG_LEVEL}")

    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.RELOAD and settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
