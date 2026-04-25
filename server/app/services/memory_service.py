"""Phase 3 in-memory conversation/task tracking service."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Dict, Any, List


class MemoryService:
    def __init__(self) -> None:
        self._conversation: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._tasks: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def add_message(self, user_id: str, role: str, content: str) -> None:
        self._conversation[user_id].append(
            {
                "role": role,
                "content": content,
                "created_at": datetime.utcnow().isoformat(),
            }
        )

    def recent_messages(self, user_id: str, limit: int = 6) -> List[Dict[str, Any]]:
        return self._conversation[user_id][-limit:]

    def add_task(self, user_id: str, title: str, status: str) -> None:
        self._tasks[user_id].append(
            {
                "title": title,
                "status": status,
                "updated_at": datetime.utcnow().isoformat(),
            }
        )

    def recent_tasks(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        return self._tasks[user_id][-limit:]
