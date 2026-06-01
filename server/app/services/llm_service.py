"""
LLM Service - Wrapper around LLM Provider
Handles communication with language models
"""

import logging
from typing import Optional, Dict, Any, List

from app.core.llm import LLMProvider

logger = logging.getLogger(__name__)


class LLMService:
    """
    Service layer for LLM interactions
    Provides structured interface to LLM provider
    """

    def __init__(self):
        """Initialize LLM service"""
        self.llm = LLMProvider()
        logger.info("✅ LLM Service initialized")

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Generate text using LLM

        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Max response length
            context: Optional context

        Returns:
            Generated text or None
        """
        return await self.llm.generate(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            context=context,
        )

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> Dict[str, Any]:
        """
        Chat completion interface

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Max response length

        Returns:
            Response dict with 'content' key
        """
        # Convert messages to single prompt
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
        content = await self.generate(prompt, temperature, max_tokens)
        
        return {
            "content": content or "",
            "model": self.llm.current_provider,
        }

    async def retrieve_relevant_context(
        self,
        user_id: str,
        query: str,
    ) -> str:
        """
        Retrieve relevant context for query
        Placeholder for future semantic search

        Args:
            user_id: User ID
            query: Query string

        Returns:
            Relevant context as string
        """
        return f"Context for {query}"
