"""
Vector Memory System - Semantic Embeddings & Retrieval
Stores and retrieves memories using vector embeddings for semantic search
"""

import logging
import json
import asyncio
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
from collections import defaultdict

try:
    from sentence_transformers import SentenceTransformer
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False

logger = logging.getLogger(__name__)


class MemoryVector:
    """Single memory with embedding"""

    def __init__(
        self,
        id: str,
        content: str,
        embedding: Optional[List[float]] = None,
        memory_type: str = "conversation",
        user_id: str = "default_user",
        importance_score: float = 0.5,
        tags: Optional[List[str]] = None,
        created_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.content = content
        self.embedding = embedding
        self.memory_type = memory_type
        self.user_id = user_id
        self.importance_score = importance_score
        self.tags = tags or []
        self.created_at = created_at or datetime.utcnow()
        self.accessed_at = datetime.utcnow()
        self.access_count = 0
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dict"""
        return {
            "id": self.id,
            "content": self.content,
            "embedding": self.embedding,
            "memory_type": self.memory_type,
            "user_id": self.user_id,
            "importance_score": self.importance_score,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "accessed_at": self.accessed_at.isoformat(),
            "access_count": self.access_count,
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "MemoryVector":
        """Create from dict"""
        m = MemoryVector(
            id=data["id"],
            content=data["content"],
            embedding=data.get("embedding"),
            memory_type=data.get("memory_type", "conversation"),
            user_id=data.get("user_id", "default_user"),
            importance_score=data.get("importance_score", 0.5),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )
        if "created_at" in data:
            m.created_at = datetime.fromisoformat(data["created_at"])
        if "accessed_at" in data:
            m.accessed_at = datetime.fromisoformat(data["accessed_at"])
        m.access_count = data.get("access_count", 0)
        return m


class VectorMemory:
    """
    Production-grade vector memory system

    Features:
    - Semantic embeddings using sentence-transformers
    - Vector similarity search
    - Memory ranking and filtering
    - Importance scoring
    - Persistent storage
    - Batch operations
    - Memory pruning
    """

    def __init__(
        self,
        data_dir: str = "data/memory",
        model_name: str = "all-MiniLM-L6-v2",
        embedding_dim: int = 384,
    ):
        """
        Initialize vector memory

        Args:
            data_dir: Directory for persistent storage
            model_name: Sentence-transformers model
            embedding_dim: Embedding dimension
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.model_name = model_name
        self.embedding_dim = embedding_dim
        self.model = None
        self.embeddings_cache = {}
        self.memory_index: Dict[str, List[MemoryVector]] = defaultdict(list)

        # Load embeddings model if available
        if HAS_EMBEDDINGS:
            try:
                logger.info(f"Loading embedding model: {model_name}")
                self.model = SentenceTransformer(model_name)
                logger.info("✅ Embedding model loaded")
            except Exception as e:
                logger.warning(f"Failed to load embedding model: {str(e)}")
                HAS_EMBEDDINGS = False
        else:
            logger.warning("sentence-transformers not installed - semantic search disabled")

        # Load persisted memories
        self._load_memories()
        logger.info("✅ Vector Memory initialized")

    async def add_memory(
        self,
        content: str,
        user_id: str,
        memory_type: str = "conversation",
        importance_score: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add memory with embedding

        Args:
            content: Memory content
            user_id: User ID
            memory_type: Type of memory
            importance_score: Importance (0-1)
            tags: Optional tags
            metadata: Optional metadata

        Returns:
            Memory ID
        """
        try:
            import hashlib

            # Generate ID
            memory_id = hashlib.md5(
                f"{user_id}{content}{datetime.utcnow()}".encode()
            ).hexdigest()

            # Generate embedding
            embedding = None
            if self.model and content:
                loop = asyncio.get_event_loop()
                embedding = await loop.run_in_executor(
                    None,
                    lambda: self.model.encode(content).tolist(),
                )
                self.embeddings_cache[memory_id] = embedding

            # Create memory
            memory = MemoryVector(
                id=memory_id,
                content=content,
                embedding=embedding,
                memory_type=memory_type,
                user_id=user_id,
                importance_score=importance_score,
                tags=tags,
                metadata=metadata,
            )

            # Store in index
            self.memory_index[user_id].append(memory)

            # Persist
            await self._persist_memory(user_id, memory)

            logger.info(f"✅ Memory added: {memory_id}")
            return memory_id

        except Exception as e:
            logger.error(f"Failed to add memory: {str(e)}", exc_info=True)
            return ""

    async def search_similar(
        self,
        query: str,
        user_id: str,
        top_k: int = 5,
        min_score: float = 0.3,
        memory_types: Optional[List[str]] = None,
    ) -> List[Tuple[MemoryVector, float]]:
        """
        Search for similar memories using semantic similarity

        Args:
            query: Search query
            user_id: User ID
            top_k: Number of results
            min_score: Minimum similarity score
            memory_types: Optional filter by memory type

        Returns:
            List of (memory, similarity_score) tuples
        """
        try:
            if not self.model or not query:
                logger.warning("Embeddings not available or empty query")
                return []

            # Encode query
            loop = asyncio.get_event_loop()
            query_embedding = await loop.run_in_executor(
                None,
                lambda: self.model.encode(query),
            )

            # Get user memories
            user_memories = self.memory_index.get(user_id, [])
            if not user_memories:
                logger.debug(f"No memories found for user {user_id}")
                return []

            # Filter by type if specified
            if memory_types:
                user_memories = [m for m in user_memories if m.memory_type in memory_types]

            # Calculate similarities
            results = []
            for memory in user_memories:
                if memory.embedding is None:
                    continue

                # Cosine similarity
                embedding_array = np.array(memory.embedding)
                query_array = np.array(query_embedding)

                similarity = np.dot(embedding_array, query_array) / (
                    np.linalg.norm(embedding_array) * np.linalg.norm(query_array) + 1e-8
                )

                # Apply importance boost
                boosted_score = similarity * (0.5 + 0.5 * memory.importance_score)

                if boosted_score >= min_score:
                    results.append((memory, float(boosted_score)))

            # Sort by score and return top_k
            results.sort(key=lambda x: x[1], reverse=True)
            
            # Update access counts
            for memory, _ in results[:top_k]:
                memory.access_count += 1
                memory.accessed_at = datetime.utcnow()

            logger.debug(f"Found {len(results)} similar memories for {user_id}")
            return results[:top_k]

        except Exception as e:
            logger.error(f"Search failed: {str(e)}", exc_info=True)
            return []

    async def get_context(
        self,
        query: str,
        user_id: str,
        max_tokens: int = 1000,
    ) -> str:
        """
        Get formatted memory context for LLM

        Args:
            query: Search query
            user_id: User ID
            max_tokens: Max context tokens

        Returns:
            Formatted context string
        """
        try:
            # Search similar memories
            results = await self.search_similar(query, user_id, top_k=5)

            if not results:
                return "No relevant memories found."

            # Build context
            context_lines = ["Recent memories:"]
            token_count = 0

            for memory, score in results:
                line = f"[{memory.memory_type} - relevance: {score:.2f}] {memory.content}"
                tokens = len(line.split()) * 1.3  # Rough estimation

                if token_count + tokens > max_tokens:
                    break

                context_lines.append(line)
                token_count += tokens

            return "\n".join(context_lines)

        except Exception as e:
            logger.error(f"Failed to get context: {str(e)}")
            return "No context available."

    async def update_importance(
        self,
        memory_id: str,
        user_id: str,
        new_importance: float,
    ) -> bool:
        """
        Update memory importance score

        Args:
            memory_id: Memory ID
            user_id: User ID
            new_importance: New importance score (0-1)

        Returns:
            Success flag
        """
        try:
            user_memories = self.memory_index.get(user_id, [])
            for memory in user_memories:
                if memory.id == memory_id:
                    memory.importance_score = max(0.0, min(1.0, new_importance))
                    await self._persist_memory(user_id, memory)
                    logger.info(f"Updated importance for {memory_id}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to update importance: {str(e)}")
            return False

    async def prune_memories(
        self,
        user_id: str,
        max_age_days: int = 30,
        min_importance: float = 0.3,
        min_access_count: int = 0,
    ) -> int:
        """
        Remove old or low-importance memories

        Args:
            user_id: User ID
            max_age_days: Remove memories older than this
            min_importance: Keep memories with importance >= this
            min_access_count: Keep memories accessed >= this many times

        Returns:
            Number of memories removed
        """
        try:
            user_memories = self.memory_index.get(user_id, [])
            cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)

            original_count = len(user_memories)
            kept_memories = []

            for memory in user_memories:
                # Keep if recent
                if memory.created_at > cutoff_date:
                    kept_memories.append(memory)
                # Keep if important
                elif memory.importance_score >= min_importance:
                    kept_memories.append(memory)
                # Keep if frequently accessed
                elif memory.access_count >= min_access_count:
                    kept_memories.append(memory)

            self.memory_index[user_id] = kept_memories
            removed = original_count - len(kept_memories)

            if removed > 0:
                logger.info(f"Pruned {removed} memories for {user_id}")
                # Re-persist user memories
                await self._repersist_user_memories(user_id)

            return removed

        except Exception as e:
            logger.error(f"Pruning failed: {str(e)}")
            return 0

    def get_stats(self, user_id: str) -> Dict[str, Any]:
        """Get memory statistics"""
        user_memories = self.memory_index.get(user_id, [])

        if not user_memories:
            return {
                "total": 0,
                "by_type": {},
                "avg_importance": 0.0,
                "total_accesses": 0,
            }

        by_type = defaultdict(int)
        total_importance = 0.0
        total_accesses = 0

        for memory in user_memories:
            by_type[memory.memory_type] += 1
            total_importance += memory.importance_score
            total_accesses += memory.access_count

        return {
            "total": len(user_memories),
            "by_type": dict(by_type),
            "avg_importance": total_importance / len(user_memories),
            "total_accesses": total_accesses,
        }

    def _load_memories(self) -> None:
        """Load memories from disk"""
        try:
            memories_file = self.data_dir / "memories.jsonl"
            if not memories_file.exists():
                logger.info("No persisted memories found")
                return

            count = 0
            with open(memories_file, "r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    memory = MemoryVector.from_dict(data)
                    self.memory_index[memory.user_id].append(memory)
                    if memory.embedding:
                        self.embeddings_cache[memory.id] = memory.embedding
                    count += 1

            logger.info(f"✅ Loaded {count} persisted memories")

        except Exception as e:
            logger.error(f"Failed to load memories: {str(e)}")

    async def _persist_memory(
        self,
        user_id: str,
        memory: MemoryVector,
    ) -> None:
        """Persist single memory to disk"""
        try:
            memories_file = self.data_dir / "memories.jsonl"
            with open(memories_file, "a") as f:
                f.write(json.dumps(memory.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"Failed to persist memory: {str(e)}")

    async def _repersist_user_memories(self, user_id: str) -> None:
        """Re-persist all memories for user"""
        try:
            # This is a simple approach - in production use a database
            memories_file = self.data_dir / "memories.jsonl"
            all_memories = []

            # Read all memories
            if memories_file.exists():
                with open(memories_file, "r") as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            if data.get("user_id") != user_id:
                                all_memories.append(line.strip())

            # Write back without user's memories
            with open(memories_file, "w") as f:
                for line in all_memories:
                    f.write(line + "\n")
                # Write updated memories
                for memory in self.memory_index[user_id]:
                    f.write(json.dumps(memory.to_dict()) + "\n")

        except Exception as e:
            logger.error(f"Failed to repersist memories: {str(e)}")
