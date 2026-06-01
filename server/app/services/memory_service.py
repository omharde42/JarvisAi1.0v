"""
Memory Service - Wrapper around Memory Manager
Provides interface for memory operations
"""

import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class MemoryService:
    """
    Service layer for memory operations
    Manages conversation and task memory
    """

    def __init__(self):
        """Initialize memory service"""
        self._conversation: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._tasks: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        logger.info("✅ Memory Service initialized")

    def add_message(
        self,
        user_id: str,
        role: str,
        content: str,
    ) -> None:
        """
        Add message to conversation history

        Args:
            user_id: User ID
            role: Message role (user, assistant, system)
            content: Message content
        """
        self._conversation[user_id].append({
            "role": role,
            "content": content,
            "created_at": datetime.utcnow().isoformat(),
        })
        logger.debug(f"Memory: added {role} message for user {user_id}")

    def recent_messages(
        self,
        user_id: str,
        limit: int = 6,
    ) -> List[Dict[str, Any]]:
        """
        Get recent messages for user

        Args:
            user_id: User ID
            limit: Number of messages to return

        Returns:
            List of recent messages
        """
        return self._conversation[user_id][-limit:]

    def add_task(
        self,
        user_id: str,
        title: str,
        status: str = "pending",
    ) -> None:
        """
        Add task to task history

        Args:
            user_id: User ID
            title: Task title
            status: Task status
        """
        self._tasks[user_id].append({
            "title": title,
            "status": status,
            "updated_at": datetime.utcnow().isoformat(),
        })
        logger.debug(f"Memory: added task '{title}' for user {user_id}")

    def recent_tasks(
        self,
        user_id: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get recent tasks for user

        Args:
            user_id: User ID
            limit: Number of tasks to return

        Returns:
            List of recent tasks
        """
        return self._tasks[user_id][-limit:]

    async def retrieve_relevant_context(
        self,
        user_id: str,
        query: str,
    ) -> str:
        """
        Retrieve relevant memory context for query

        Args:
            user_id: User ID
            query: Query string

        Returns:
            Relevant context
        """
        messages = self.recent_messages(user_id, limit=5)
        context_lines = [f"{m['role']}: {m['content']}" for m in messages]
        return "\n".join(context_lines) if context_lines else "No context available"
