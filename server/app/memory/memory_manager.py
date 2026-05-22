from typing import List, Dict

from app.memory.database import (
    get_connection,
    initialize_database,
)


class MemoryManager:
    """
    Persistent Memory System
    """

    def __init__(self):
        initialize_database()

    async def store_memory(
        self,
        user_message: str,
        ai_response: str,
    ):
        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO memories (
            user_message,
            ai_response
        )
        VALUES (?, ?)
        """, (user_message, ai_response))

        conn.commit()
        conn.close()

    async def get_recent_memories(
        self,
        limit: int = 5
    ) -> List[Dict]:

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM memories
        ORDER BY id DESC
        LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()

        conn.close()

        return [dict(row) for row in rows]
