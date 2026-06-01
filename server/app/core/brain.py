"""
Jarvis Brain - Main AI Processing Engine
Production-ready async brain with error handling, retries, and caching
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.config import settings
from app.core.llm import LLMProvider
from app.core.agent_runtime import AgentRuntime
from app.core.cache import ResponseCache

logger = logging.getLogger(__name__)


class JarvisBrain:
    """
    Main AI Brain System

    Features:
    - Multi-provider LLM support (Gemini, OpenAI)
    - Response caching with TTL
    - Agent-based task execution
    - Error recovery and fallback
    - Comprehensive logging and metrics
    """

    def __init__(self):
        """Initialize brain with all subsystems"""
        try:
            self.llm = LLMProvider()
            self.agent = AgentRuntime()
            self.cache = ResponseCache(
                max_size=settings.CACHE_MAX_SIZE,
                default_ttl=settings.CACHE_TTL,
            )
            logger.info("🧠 Jarvis Brain Initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Jarvis Brain: {str(e)}", exc_info=True)
            raise

    async def process(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        user_id: str = "default_user",
    ) -> Dict[str, Any]:
        """
        Main processing pipeline

        Args:
            prompt: User prompt/request
            context: Optional context data
            use_cache: Whether to use cached responses
            user_id: User identifier

        Returns:
            Standardized response with success/error info
        """

        start_time = datetime.utcnow()

        # =========================
        # VALIDATION
        # =========================

        if not prompt:
            logger.warning("Empty prompt received")
            return self._error_response(
                "Prompt is empty",
                "validation_error"
            )

        prompt = prompt.strip()
        logger.info(f"📩 Processing Prompt: {prompt[:100]}...")

        try:
            # =========================
            # CHECK CACHE
            # =========================

            if use_cache and settings.ENABLE_RESPONSE_CACHE:
                cached_response = self.cache.get(prompt)
                if cached_response:
                    logger.info("✅ Returning cached response")
                    return {
                        **cached_response,
                        "cached": True,
                    }

            # =========================
            # AGENT EXECUTION
            # =========================

            try:
                agent_result = await asyncio.wait_for(
                    self.agent.run(prompt, user_id=user_id, context=context),
                    timeout=settings.LLM_TIMEOUT,
                )
                logger.info("✅ Agent execution completed")
            except asyncio.TimeoutError:
                logger.warning("Agent execution timed out, skipping")
                agent_result = {"error": "Agent timeout"}
            except Exception as e:
                logger.warning(f"Agent execution failed: {str(e)}")
                agent_result = {"error": str(e)}

            # =========================
            # LLM GENERATION WITH RETRIES
            # =========================

            response = None
            last_error = None

            for attempt in range(settings.MAX_RETRIES + 1):
                try:
                    logger.info(f"LLM generation attempt {attempt + 1}/{settings.MAX_RETRIES + 1}")

                    response = await asyncio.wait_for(
                        self.llm.generate(
                            prompt=prompt,
                            temperature=settings.LLM_TEMPERATURE,
                            max_tokens=settings.LLM_MAX_TOKENS,
                            context=context,
                        ),
                        timeout=settings.LLM_TIMEOUT,
                    )

                    if response:
                        break

                except asyncio.TimeoutError:
                    last_error = "LLM request timed out"
                    logger.warning(f"LLM timeout on attempt {attempt + 1}")

                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"LLM error on attempt {attempt + 1}: {last_error}")

                # Wait before retry
                if attempt < settings.MAX_RETRIES:
                    await asyncio.sleep(settings.RETRY_DELAY)

            # =========================
            # FALLBACK
            # =========================

            if not response:
                if settings.ENABLE_FALLBACK_MODE:
                    logger.info("Using fallback response")
                    response = self._fallback_response(prompt)
                else:
                    logger.error(f"LLM generation failed: {last_error}")
                    return self._error_response(
                        last_error or "LLM generation failed",
                        "llm_error"
                    )

            thinking_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )

            logger.info(f"✅ Response generated in {thinking_time}ms")

            # Build success response
            result = {
                "success": True,
                "response": response,
                "thinking_time_ms": thinking_time,
                "model_used": self.llm.current_provider,
                "cached": False,
                "agent": agent_result,
                "error": None,
            }

            # Cache response
            if settings.ENABLE_RESPONSE_CACHE:
                self.cache.set(prompt, result, ttl=settings.CACHE_TTL)

            return result

        except asyncio.TimeoutError:
            logger.error("❌ Brain processing timeout")
            return self._error_response(
                "Request timed out",
                "timeout_error"
            )

        except Exception as e:
            logger.error(
                f"❌ Brain processing error: {str(e)}",
                exc_info=True
            )
            return self._error_response(
                str(e),
                "system_error"
            )

    def _fallback_response(self, prompt: str) -> str:
        """
        Safe fallback response when LLM fails

        Args:
            prompt: User prompt

        Returns:
            Fallback response text
        """

        prompt_lower = prompt.lower()

        if any(word in prompt_lower for word in ["hi", "hello", "hey"]):
            return "Hello! I am Jarvis, your AI assistant. How can I help you today?"

        if "help" in prompt_lower:
            return "I can help with planning, searching, calculations, coding, and AI tasks. What would you like to do?"

        if "status" in prompt_lower or "health" in prompt_lower:
            return "I'm operational and ready to help!"

        return f"I received your request about: {prompt[:100]}. I'm processing it and will provide a response shortly."

    def _error_response(
        self,
        message: str,
        error_type: str,
    ) -> Dict[str, Any]:
        """
        Standardized error response

        Args:
            message: Error message
            error_type: Type of error

        Returns:
            Error response dict
        """

        return {
            "success": False,
            "response": None,
            "thinking_time_ms": 0,
            "model_used": None,
            "cached": False,
            "agent": None,
            "error": {
                "type": error_type,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        System health check

        Returns:
            Health status with component info
        """

        return {
            "status": "healthy",
            "llm_provider": self.llm.current_provider,
            "llm_available": {
                "gemini": self.llm.gemini_available,
                "openai": self.llm.openai_available,
            },
            "agent_runtime": "active",
            "cache_stats": self.cache.stats(),
            "timestamp": datetime.utcnow().isoformat(),
        }
