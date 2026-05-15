"""
Middleware - Request/Response processing
Logging, tracing, rate limiting, CORS
"""

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging
import time
import uuid
from typing import Callable

logger = logging.getLogger(__name__)


class RequestTracingMiddleware:
    """
    Add request tracing and logging
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process request with tracing"""
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Log request
        logger.info(
            f"📨 {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
            },
        )

        # Process request
        start_time = time.time()
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(
                f"❌ Request failed: {str(e)}",
                extra={"request_id": request_id},
                exc_info=True,
            )
            raise

        # Calculate processing time
        process_time = time.time() - start_time

        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)

        # Log response
        logger.info(
            f"✅ {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time": process_time,
            },
        )

        return response


def setup_middleware(app):
    """
    Setup all middleware for the FastAPI app
    """

    # Request tracing
    app.middleware("http")(RequestTracingMiddleware(app))

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure based on environment
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Trusted hosts
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1"],
    )

    logger.info("✅ Middleware configured")
