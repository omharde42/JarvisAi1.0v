"""
Configuration Management
Loads environment variables and provides centralized app settings
"""

from pydantic_settings import BaseSettings
from pydantic import Field
import os
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from .env file
    Uses Pydantic v2 for validation and type safety
    """

    # ========================================================================
    # APPLICATION SETTINGS
    # ========================================================================
    APP_NAME: str = Field(default="Jarvis AI Assistant", description="Application name")
    APP_VERSION: str = Field(default="2.0.0", description="Application version")
    ENVIRONMENT: str = Field(default="development", description="Environment (development/staging/production)")
    DEBUG: bool = Field(default=True, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    API_VERSION: str = Field(default="v1", description="API version")

    # ========================================================================
    # SERVER SETTINGS
    # ========================================================================
    SERVER_HOST: str = Field(default="0.0.0.0", description="Server host")
    SERVER_PORT: int = Field(default=8000, description="Server port")
    RELOAD: bool = Field(default=False, description="Auto-reload on file changes")
    WORKERS: int = Field(default=4, description="Number of worker processes")

    # ========================================================================
    # SECURITY
    # ========================================================================
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production", description="Secret key for JWT")
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration")
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="Max requests per window")
    RATE_LIMIT_WINDOW_SECONDS: int = Field(default=60, description="Rate limit window")

    # ========================================================================
    # DATABASE
    # ========================================================================
    DATABASE_URL: Optional[str] = Field(
        default="sqlite:///./jarvis.db",
        description="Database URL (supports SQLite, PostgreSQL, MySQL)",
    )
    DATABASE_ECHO: bool = Field(default=False, description="Echo SQL queries")
    DATABASE_POOL_SIZE: int = Field(default=5, description="Database connection pool size")

    # ========================================================================
    # LLM PROVIDERS
    # ========================================================================
    # Google Gemini
    GOOGLE_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API Key")
    GEMINI_MODEL: str = Field(default="gemini-2.0-flash", description="Gemini model name")

    # OpenAI (fallback)
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API Key")
    OPENAI_MODEL: str = Field(default="gpt-4-turbo", description="OpenAI model name")

    # ========================================================================
    # LLM CONFIGURATION
    # ========================================================================
    LLM_TIMEOUT: int = Field(default=30, description="LLM request timeout in seconds")
    LLM_MAX_TOKENS: int = Field(default=2048, description="Maximum tokens in response")
    LLM_TEMPERATURE: float = Field(default=0.7, description="Temperature for response generation")
    LLM_TOP_P: float = Field(default=0.9, description="Top-p for nucleus sampling")
    LLM_PRESENCE_PENALTY: float = Field(default=0.0, description="Presence penalty")
    LLM_FREQUENCY_PENALTY: float = Field(default=0.0, description="Frequency penalty")

    # ========================================================================
    # FALLBACK & SAFETY
    # ========================================================================
    ENABLE_FALLBACK_MODE: bool = Field(default=True, description="Enable fallback when LLM fails")
    MAX_RETRIES: int = Field(default=3, description="Max retries for LLM calls")
    RETRY_DELAY: float = Field(default=1.0, description="Delay between retries in seconds")
    ENABLE_STREAMING: bool = Field(default=False, description="Enable response streaming")

    # ========================================================================
    # CACHING
    # ========================================================================
    ENABLE_RESPONSE_CACHE: bool = Field(default=True, description="Cache responses")
    CACHE_TTL: int = Field(default=3600, description="Cache TTL in seconds")
    CACHE_MAX_SIZE: int = Field(default=1000, description="Max cache entries")

    # ========================================================================
    # MEMORY SYSTEM
    # ========================================================================
    MEMORY_ENABLED: bool = Field(default=True, description="Enable memory system")
    MEMORY_MAX_HISTORY: int = Field(default=50, description="Max conversation history per user")
    MEMORY_COMPRESSION_ENABLED: bool = Field(default=True, description="Enable memory compression")

    # ========================================================================
    # TOOLS
    # ========================================================================
    TOOLS_ENABLED: bool = Field(default=True, description="Enable tool system")
    TOOLS_TIMEOUT: int = Field(default=30, description="Tool execution timeout")
    TOOLS_SANDBOX_ENABLED: bool = Field(default=True, description="Enable tool sandboxing")

    # ========================================================================
    # OBSERVABILITY
    # ========================================================================
    METRICS_ENABLED: bool = Field(default=True, description="Enable metrics collection")
    TRACING_ENABLED: bool = Field(default=False, description="Enable distributed tracing")
    SENTRY_DSN: Optional[str] = Field(default=None, description="Sentry DSN for error tracking")

    class Config:
        """Pydantic config"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
