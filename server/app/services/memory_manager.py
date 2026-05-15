"""
Memory Management System
Handles short-term, long-term, and semantic memory with persistence
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class MemoryEntry:
    """
    Single memory entry with metadata
    """

    def __init__(
        self,
        content: str,
        memory_type: str = "conversation",
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ):
        self.id = hashlib.md5(f"{user_id}{content}{datetime.utcnow()}".encode()).hexdigest()
        self.content = content
        self.memory_type = memory_type  # conversation, knowledge, preference, project
        self.user_id = user_id
        self.tags = tags or []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.access_count = 0
        self.importance = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "content": self.content,
            "type": self.memory_type,
            "user_id": self.user_id,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "access_count": self.access_count,
            "importance": self.importance,
        }


class MemoryManager:
    """
    Production-grade memory management system

    Features:
    - Short-term memory (conversation history)
    - Long-term memory (persistent storage)
    - Semantic memory (context retrieval)
    - Memory compression and cleanup
    - User-specific memory isolation
    """

    def __init__(self, data_dir: str = "data/memory"):
        """
        Initialize memory manager
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # In-memory caches
        self.short_term: Dict[str, List[MemoryEntry]] = {}
        self.long_term: Dict[str, List[MemoryEntry]] = {}
        self.semantic_memory: Dict[str, List[MemoryEntry]] = {}

        logger.info("✅ Memory Manager initialized")

    async def store_memory(
        self,
        user_id: str,
        content: str,
        memory_type: str = "conversation",
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Store a new memory entry

        Args:
            user_id: User ID
            content: Memory content
            memory_type: Type of memory (conversation, knowledge, preference, project)
            tags: Optional tags for categorization

        Returns:
            Memory ID
        """
        try:
            # Create memory entry
            entry = MemoryEntry(
                content=content,
                memory_type=memory_type,
                user_id=user_id,
                tags=tags,
            )

            # Store in appropriate cache
            if memory_type == "conversation":
                if user_id not in self.short_term:
                    self.short_term[user_id] = []
                self.short_term[user_id].append(entry)
            else:
                if user_id not in self.long_term:
                    self.long_term[user_id] = []
                self.long_term[user_id].append(entry)

            # Persist to disk
            await self._persist_memory(user_id, entry)

            logger.info(f"💾 Memory stored - User: {user_id}, Type: {memory_type}")
            return entry.id

        except Exception as e:
            logger.error(f"Failed to store memory: {str(e)}", exc_info=True)
            raise

    async def retrieve_memory(
        self,
        user_id: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve user memories

        Args:
            user_id: User ID
            memory_type: Optional filter by type
            limit: Maximum entries to return

        Returns:
            List of memory entries
        """
        results = []

        # Retrieve from short-term
        if user_id in self.short_term:
            for entry in self.short_term[user_id][-limit:]:
                if memory_type is None or entry.memory_type == memory_type:
                    results.append(entry.to_dict())

        # Retrieve from long-term if needed
        if len(results) < limit and user_id in self.long_term:
            for entry in self.long_term[user_id][-limit:]:
                if memory_type is None or entry.memory_type == memory_type:
                    if entry.id not in [r["id"] for r in results]:
                        results.append(entry.to_dict())

        logger.debug(f"📖 Retrieved {len(results)} memories for user {user_id}")
        return results

    async def search_memory(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search memories by content (simple keyword matching for now)
        Production version would use semantic search with embeddings

        Args:
            user_id: User ID
            query: Search query
            limit: Maximum results

        Returns:
            Matching memory entries
        """
        results = []
        query_lower = query.lower()

        # Search in all user memories
        for memory_list in [self.short_term.get(user_id, []), self.long_term.get(user_id, [])]:
            for entry in memory_list:
                if query_lower in entry.content.lower():
                    entry.access_count += 1  # Track access for importance
                    results.append(entry.to_dict())

        logger.debug(f"🔍 Search found {len(results)} matches for user {user_id}")
        return results[:limit]

    async def clear_memory(
        self,
        user_id: str,
        memory_type: Optional[str] = None,
    ) -> int:
        """
        Clear user memories

        Args:
            user_id: User ID
            memory_type: Optional specific type to clear

        Returns:
            Number of entries cleared
        """
        count = 0

        if memory_type is None or memory_type == "conversation":
            count += len(self.short_term.get(user_id, []))
            self.short_term.pop(user_id, None)

        if memory_type is None or memory_type != "conversation":
            count += len(self.long_term.get(user_id, []))
            self.long_term.pop(user_id, None)

        logger.info(f"🗑️ Cleared {count} memories for user {user_id}")
        return count

    async def get_conversation_context(
        self,
        user_id: str,
        max_tokens: int = 2000,
    ) -> str:
        """
        Get formatted conversation context for LLM
        Returns recent conversation history up to max_tokens

        Args:
            user_id: User ID
            max_tokens: Maximum tokens in context

        Returns:
            Formatted conversation context
        """
        memories = await self.retrieve_memory(
            user_id,
            memory_type="conversation",
            limit=50,
        )

        context_lines = []
        token_count = 0
        estimated_tokens_per_line = 5

        for memory in reversed(memories):
            line = f"{memory['created_at']}: {memory['content']}"
            tokens = len(line.split()) * estimated_tokens_per_line

            if token_count + tokens > max_tokens:
                break

            context_lines.insert(0, line)
            token_count += tokens

        return "\n".join(context_lines) if context_lines else "No previous context"

    async def compress_memory(self, user_id: str) -> int:
        """
        Compress/cleanup old memories
        Keeps high-importance entries, removes low-importance ones

        Returns:
            Number of entries removed
        """
        removed = 0
        cutoff_date = datetime.utcnow() - timedelta(days=30)

        # Process short-term memory
        if user_id in self.short_term:
            original_count = len(self.short_term[user_id])
            self.short_term[user_id] = [
                entry
                for entry in self.short_term[user_id]
                if entry.created_at > cutoff_date or entry.importance > 0.5
            ]
            removed += original_count - len(self.short_term[user_id])

        # Process long-term memory
        if user_id in self.long_term:
            original_count = len(self.long_term[user_id])
            self.long_term[user_id] = [
                entry
                for entry in self.long_term[user_id]
                if entry.importance > 0.3
            ]
            removed += original_count - len(self.long_term[user_id])

        logger.info(f"🧹 Memory compression removed {removed} entries for user {user_id}")
        return removed

    async def _persist_memory(self, user_id: str, entry: MemoryEntry) -> None:
        """
        Persist memory entry to disk
        """
        try:
            user_dir = self.data_dir / user_id
            user_dir.mkdir(parents=True, exist_ok=True)

            # Save to user's memory file
            memory_file = user_dir / f"{entry.memory_type}_memory.jsonl"
            with open(memory_file, "a") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")

        except Exception as e:
            logger.error(f"Failed to persist memory: {str(e)}")


# Global memory manager
memory_manager: Optional[MemoryManager] = None


async def get_memory_manager() -> MemoryManager:
    """
    Get or create global memory manager
    """
    global memory_manager
    if memory_manager is None:
        memory_manager = MemoryManager()
    return memory_manager
