from typing import List


class MemoryManager:
    """
    Temporary memory system
    """

    def __init__(self):
        self.memory: List[str] = []

    async def store(self, text: str):
        self.memory.append(text)

    async def get_all(self):
        return self.memory
