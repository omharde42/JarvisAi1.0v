"""
Jarvis Brain - AI Processing Engine
Handles async LLM integration with fallback support and caching
"""

import asyncio
import logging
from typing import Optional, Dict, Any
import hashlib
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.llm import LLMProvider

logger = logging.getLogger(__name__)


class ResponseCache:
    """
    Simple in-memory response cache with TTL
    """

    def __init__(self, ttl_seconds: int = 3600):
        self.cache: Dict[str, tuple[str, datetime]] = {}
        self.ttl = ttl_seconds

    def _hash_prompt(self, prompt: str) -> str:
        """Generate cache key from prompt"""
        return hashlib.md5(prompt.encode()).hexdigest()

    def get(self, prompt: str) -> Optional[str]:
        """Get cached response if valid"""
        key = self._hash_prompt(prompt)

        if key in self.cache:
            response, timestamp = self.cache[key]
            if datetime.utcnow() - timestamp < timedelta(seconds=self.ttl):
                logger.debug(f"Cache hit for prompt: {prompt[:50]}...")
                return response
            else:
                del self.cache[key]

        return None

    def set(self, prompt: str, response: str) -> None:
        """Cache a response"""
        key = self._hash_prompt(prompt)
        self.cache[key] = (response, datetime.utcnow())
        logger.debug(f"Cached response for prompt: {prompt[:50]}...")

    def clear(self) -> None:
        """Clear cache"""
        self.cache.clear()
        logger.info("Cache cleared")


class JarvisBrain:
    """
    AI Brain - Main processing engine

    Features:
    - Async LLM integration (Google Gemini + OpenAI)
    - Automatic fallback on failure
    - Response caching
    - Error handling and retry logic
    - Structured logging
    """

    def __init__(self):
        """
        Initialize Jarvis Brain with LLM provider and cache
        """
        self.llm = LLMProvider()
        self.cache = ResponseCache(ttl_seconds=settings.CACHE_TTL) if settings.ENABLE_RESPONSE_CACHE else None
        logger.info("🧠 Jarvis Brain initialized")

    async def process(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Process a prompt and return structured response

        Args:
            prompt: User input/question
            context: Optional context data
            use_cache: Whether to use cached responses

        Returns:
            Response dict with:
            {
                "success": bool,
                "response": str,
                "thinking_time_ms": int,
                "model_used": str,
                "cached": bool,
                "error": Optional[str]
            }
        """

        # Validate input
        if not prompt or not isinstance(prompt, str):
            logger.warning("Invalid prompt received")
            return self._error_response("Invalid prompt", error_type="validation_error")

        prompt = prompt.strip()
        if not prompt:
            logger.warning("Empty prompt received")
            return self._error_response("Prompt cannot be empty", error_type="validation_error")

        # Check cache
        if use_cache and self.cache:
            cached_response = self.cache.get(prompt)
            if cached_response:
                return {
                    "success": True,
                    "response": cached_response,
                    "thinking_time_ms": 0,
                    "model_used": "cache",
                    "cached": True,
                    "error": None,
                }

        logger.info(f"Processing prompt: {prompt[:100]}...")
        start_time = datetime.utcnow()

        try:
            # Try to get response from LLM
            response = await self._process_with_retry(prompt, context)

            if response:
                # Cache successful response
                if self.cache:
                    self.cache.set(prompt, response)

                thinking_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

                result = {
                    "success": True,
                    "response": response,
                    "thinking_time_ms": thinking_time_ms,
                    "model_used": self.llm.current_provider,
                    "cached": False,
                    "error": None,
                }
                logger.info(f"✅ Response generated in {thinking_time_ms}ms")
                return result
            else:
                return self._error_response("Failed to generate response", error_type="generation_error")

        except asyncio.TimeoutError:
            logger.error("LLM request timed out")
            return self._error_response(
                f"Request timed out (>{settings.LLM_TIMEOUT}s)",
                error_type="timeout_error",
            )

        except Exception as e:
            logger.error(f"Unexpected error in brain.process(): {str(e)}", exc_info=True)
            return self._error_response(str(e), error_type="system_error")

    async def _process_with_retry(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Process prompt with retry logic
        Attempts LLM call and retries on failure
        """

        last_error = None
        max_attempts = settings.MAX_RETRIES + 1

        for attempt in range(max_attempts):
            try:
                logger.debug(f"LLM attempt {attempt + 1}/{max_attempts}")

                # Call LLM with timeout
                response = await asyncio.wait_for(
                    self.llm.generate(
                        prompt=prompt,
                        temperature=settings.LLM_TEMPERATURE,
                        max_tokens=settings.LLM_MAX_TOKENS,
                        context=context,
                    ),
                    timeout=settings.LLM_TIMEOUT,
                )

                if response and isinstance(response, str):
                    return response

            except asyncio.TimeoutError:
                last_error = f"Timeout on attempt {attempt + 1}"
                logger.warning(last_error)

            except Exception as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1} failed: {last_error}")

            # Wait before retry (except on last attempt)
            if attempt < max_attempts - 1:
                await asyncio.sleep(settings.RETRY_DELAY)

        # All attempts failed, try fallback
        if settings.ENABLE_FALLBACK_MODE:
            logger.info("All LLM attempts failed, using fallback mode")
            return self._fallback_response(prompt, last_error)

        return None

    def _fallback_response(self, prompt: str, error: str) -> str:
        """
        Generate fallback response when LLM fails
        Safe, predictable responses that never crash
        """

        fallback_responses = {
            "greeting": "Hello! I'm Jarvis, your AI assistant. How can I help you today?",
            "help": "I can assist you with various tasks. Please ask me something specific.",
            "status": "I'm running at optimal capacity. Ready to assist.",
            "default": f"I received your message: '{prompt[:50]}...'. I'm processing it now.",
        }

        prompt_lower = prompt.lower()

        # Simple pattern matching for common prompts
        if any(word in prompt_lower for word in ["hi", "hello", "hey"]):
            return fallback_responses["greeting"]
        elif any(word in prompt_lower for word in ["help", "what can you", "how do"]):
            return fallback_responses["help"]
        elif any(word in prompt_lower for word in ["status", "how are you"]):
            return fallback_responses["status"]
        else:
            return fallback_responses["default"]

    def _error_response(
        self,
        error_message: str,
        error_type: str = "general_error",
    ) -> Dict[str, Any]:
        """
        Generate structured error response
        Never returns raw exceptions to avoid crashes
        """

        return {
            "success": False,
            "response": None,
            "thinking_time_ms": 0,
            "model_used": None,
            "cached": False,
            "error": {
                "type": error_type,
                "message": error_message,
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        Check brain health
        """

        try:
            # Test LLM connection
            test_response = await asyncio.wait_for(
                self.llm.generate(
                    prompt="Test",
                    temperature=0.5,
                    max_tokens=10,
                ),
                timeout=5,
            )

            return {
                "status": "healthy",
                "llm_provider": self.llm.current_provider,
                "cache_enabled": self.cache is not None,
                "fallback_enabled": settings.ENABLE_FALLBACK_MODE,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.warning(f"Health check failed: {str(e)}")
            return {
                "status": "degraded",
                "error": str(e),
                "fallback_available": settings.ENABLE_FALLBACK_MODE,
                "timestamp": datetime.utcnow().isoformat(),
            }
