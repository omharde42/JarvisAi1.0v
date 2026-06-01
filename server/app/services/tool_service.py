"""
Tool Service - Tool routing and management
Routes user requests to appropriate tools
"""

from typing import Dict, Any

import logging

logger = logging.getLogger(__name__)


class ToolService:
    """
    Service for routing requests to tools
    Determines which tool to use for a given task
    """

    def route(self, user_input: str) -> Dict[str, Any]:
        """
        Route user input to appropriate tool

        Args:
            user_input: User request text

        Returns:
            Tool routing decision
        """
        text = user_input.lower()

        # Code generation
        if any(k in text for k in ["code", "write", "generate", "python", "script", "function"]):
            logger.info("Routing to code tool")
            return {
                "action": "write_code",
                "status": "ready",
                "message": "Code tool selected. Provide your coding requirement.",
                "data": {"tool": "code"},
            }

        # Browser/web operations
        if any(k in text for k in ["browser", "open", "website", "url", "search", "google"]):
            logger.info("Routing to browser tool")
            return {
                "action": "open_browser",
                "status": "ready",
                "message": "Browser tool selected. Share the URL to open.",
                "data": {"tool": "browser"},
            }

        # Task execution
        if any(k in text for k in ["task", "run", "execute", "do this", "perform"]):
            logger.info("Routing to task runner")
            return {
                "action": "run_task",
                "status": "queued",
                "message": "Task tool selected. Task captured and queued.",
                "data": {"tool": "task-runner"},
            }

        # Calculator
        if any(k in text for k in ["calculate", "math", "compute", "equation"]):
            logger.info("Routing to calculator")
            return {
                "action": "calculate",
                "status": "ready",
                "message": "Calculator selected. Provide the mathematical expression.",
                "data": {"tool": "calculator"},
            }

        # Memory operations
        if any(k in text for k in ["remember", "memorize", "save", "store", "note"]):
            logger.info("Routing to memory tool")
            return {
                "action": "store_memory",
                "status": "ready",
                "message": "Memory tool selected. What should I remember?",
                "data": {"tool": "memory"},
            }

        # Default to chat
        logger.info("No direct tool matched, routing to chat")
        return {
            "action": "chat",
            "status": "fallback",
            "message": "No direct tool matched; using chat mode.",
            "data": {"tool": "llm"},
        }
