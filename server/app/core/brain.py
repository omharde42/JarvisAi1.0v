
"""
Jarvis Brain - Main AI Processing Engine
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.config import settings
from app.core.llm import LLMProvider
from app.core.agent_runtime import AgentRuntime

logger = logging.getLogger(__name__)


class JarvisBrain:
    """
    Main AI Brain System
    """

    def __init__(self):
        self.llm = LLMProvider()
        self.agent = AgentRuntime()

        logger.info("🧠 Jarvis Brain Initialized")

    async def process(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Main processing pipeline
        """

        start_time = datetime.utcnow()

        # =========================
        # VALIDATION
        # =========================

        if not prompt:
            return self._error_response(
                "Prompt is empty",
                "validation_error"
            )

        prompt = prompt.strip()

        logger.info(f"📩 Processing Prompt: {prompt}")

        try:

            # =========================
            # AGENT EXECUTION
            # =========================

            agent_result = await self.agent.run(prompt)

            # =========================
            # AI GENERATION
            # =========================

            response = await asyncio.wait_for(
                self.llm.generate(
                    prompt=prompt,
                    temperature=settings.LLM_TEMPERATURE,
                    max_tokens=settings.LLM_MAX_TOKENS,
                    context=context,
                ),
                timeout=settings.LLM_TIMEOUT,
            )

            # =========================
            # FALLBACK
            # =========================

            if not response:
                response = self._fallback_response(prompt)

            thinking_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )

            logger.info(f"✅ Response Generated in {thinking_time}ms")

            return {
                "success": True,
                "response": response,
                "thinking_time_ms": thinking_time,
                "model_used": self.llm.current_provider,
                "cached": False,
                "agent": agent_result,
                "error": None,
            }

        except asyncio.TimeoutError:

            logger.error("❌ LLM Timeout Error")

            return self._error_response(
                "Request timed out",
                "timeout_error"
            )

        except Exception as e:

            logger.error(
                f"❌ Brain Processing Error: {str(e)}",
                exc_info=True
            )

            return self._error_response(
                str(e),
                "system_error"
            )

    def _fallback_response(self, prompt: str) -> str:
        """
        Safe fallback response
        """

        prompt_lower = prompt.lower()

        if any(word in prompt_lower for word in ["hi", "hello", "hey"]):
            return "Hello! I am Jarvis. How can I help you today?"

        if "help" in prompt_lower:
            return "I can help with planning, searching, calculations, and AI tasks."

        return f"I received your request: {prompt}"

    def _error_response(
        self,
        message: str,
        error_type: str,
    ) -> Dict[str, Any]:
        """
        Standardized error response
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

    async def health_check(self):
        """
        System health check
        """

        return {
            "status": "healthy",
            "llm_provider": self.llm.current_provider,
            "agent_runtime": "active",
            "timestamp": datetime.utcnow().isoformat(),
        }

