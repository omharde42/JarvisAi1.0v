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
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    ENVIRONMENT: str = Field(default="development", description="Environment (development/staging/production)")
    DEBUG: bool = Field(default=True, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # ========================================================================
    # SERVER SETTINGS
    # ========================================================================
    SERVER_HOST: str = Field(default="0.0.0.0", description="Server host")
    SERVER_PORT: int = Field(default=8000, description="Server port")
    RELOAD: bool = Field(default=False, description="Auto-reload on file changes")

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
    LLM_MAX_TOKENS: int = Field(default=1024, description="Maximum tokens in response")
    LLM_TEMPERATURE: float = Field(default=0.7, description="Temperature for response generation")
    LLM_TOP_P: float = Field(default=0.9, description="Top-p for nucleus sampling")

    # ========================================================================
    # FALLBACK & SAFETY
    # ========================================================================
    ENABLE_FALLBACK_MODE: bool = Field(default=True, description="Enable fallback when LLM fails")
    MAX_RETRIES: int = Field(default=2, description="Max retries for LLM calls")
    RETRY_DELAY: int = Field(default=1, description="Delay between retries in seconds")

    # ========================================================================
    # CACHING
    # ========================================================================
    ENABLE_RESPONSE_CACHE: bool = Field(default=True, description="Cache responses")
    CACHE_TTL: int = Field(default=3600, description="Cache TTL in seconds")

    class Config:
        """Pydantic config"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
