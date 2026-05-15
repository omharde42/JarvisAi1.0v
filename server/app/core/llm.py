"""
LLM Provider - Multi-provider LLM integration
Supports Google Gemini and OpenAI with automatic fallback
"""

import asyncio
import logging
from typing import Optional, Dict, Any
import json

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMProvider:
    """
    Multi-provider LLM integration

    Features:
    - Primary: Google Gemini
    - Fallback: OpenAI
    - Automatic provider switching on failure
    """

    def __init__(self):
        """
        Initialize LLM provider with available models
        """
        self.current_provider = "gemini"  # Default provider
        self.gemini_available = self._check_gemini()
        self.openai_available = self._check_openai()

        if not self.gemini_available and not self.openai_available:
            logger.warning("⚠️  No LLM providers available!")

        logger.info(
            f"LLM Provider initialized - Gemini: {self.gemini_available}, OpenAI: {self.openai_available}"
        )

    def _check_gemini(self) -> bool:
        """
        Check if Google Gemini is available
        """
        try:
            if not settings.GOOGLE_API_KEY:
                logger.debug("Gemini API key not configured")
                return False

            import google.generativeai as genai
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            logger.info("✅ Google Gemini API configured")
            return True

        except ImportError:
            logger.warning("google-generativeai not installed")
            return False
        except Exception as e:
            logger.error(f"Failed to configure Gemini: {str(e)}")
            return False

    def _check_openai(self) -> bool:
        """
        Check if OpenAI is available
        """
        try:
            if not settings.OPENAI_API_KEY:
                logger.debug("OpenAI API key not configured")
                return False

            import openai
            openai.api_key = settings.OPENAI_API_KEY
            logger.info("✅ OpenAI API configured")
            return True

        except ImportError:
            logger.debug("openai not installed")
            return False
        except Exception as e:
            logger.error(f"Failed to configure OpenAI: {str(e)}")
            return False

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Generate response using available LLM

        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum response length
            context: Optional context data

        Returns:
            Generated response or None on failure
        """

        # Try primary provider (Gemini)
        if self.gemini_available:
            response = await self._generate_gemini(prompt, temperature, max_tokens)
            if response:
                self.current_provider = "gemini"
                return response

        # Fallback to OpenAI
        if self.openai_available:
            response = await self._generate_openai(prompt, temperature, max_tokens)
            if response:
                self.current_provider = "openai"
                return response

        # No providers available
        logger.error("No LLM providers available")
        return None

    async def _generate_gemini(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> Optional[str]:
        """
        Generate using Google Gemini
        """
        try:
            import google.generativeai as genai

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                    "top_p": settings.LLM_TOP_P,
                },
            )

            response = await loop.run_in_executor(
                None,
                lambda: model.generate_content(prompt),
            )

            if response and hasattr(response, "text"):
                text = response.text.strip()
                if text:
                    logger.debug("✅ Gemini response generated")
                    return text

        except Exception as e:
            logger.warning(f"Gemini generation failed: {str(e)}")

        return None

    async def _generate_openai(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> Optional[str]:
        """
        Generate using OpenAI
        """
        try:
            import openai

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()

            response = await loop.run_in_executor(
                None,
                lambda: openai.ChatCompletion.create(
                    model=settings.OPENAI_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                ),
            )

            if response and "choices" in response and len(response["choices"]) > 0:
                text = response["choices"][0]["message"]["content"].strip()
                if text:
                    logger.debug("✅ OpenAI response generated")
                    return text

        except Exception as e:
            logger.warning(f"OpenAI generation failed: {str(e)}")

        return None
