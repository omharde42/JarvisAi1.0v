"""
Application startup script
Runs Jarvis AI FastAPI server
"""

import uvicorn
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    print("\n" + "="*70)
    print(f"🤖 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print("="*70)
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Server: {settings.SERVER_HOST}:{settings.SERVER_PORT}")
    print(f"Debug: {settings.DEBUG}")
    print(f"LLM Timeout: {settings.LLM_TIMEOUT}s")
    print(f"Cache Enabled: {settings.ENABLE_RESPONSE_CACHE}")
    print(f"Fallback Mode: {settings.ENABLE_FALLBACK_MODE}")
    print("="*70)
    print("📖 API Docs: http://localhost:8000/api/docs")
    print("📊 Health: http://localhost:8000/health")
    print("💬 Process: POST http://localhost:8000/process")
    print("="*70 + "\n")

    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.RELOAD and settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
