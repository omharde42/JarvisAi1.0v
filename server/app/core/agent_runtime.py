from app.planner.planner import TaskPlanner
from app.memory.memory_manager import MemoryManager
from app.tools.tool_registry import ToolRegistry


class AgentRuntime:
    """
    Main autonomous execution runtime
    """

    def __init__(self):
        self.planner = TaskPlanner()
        self.memory = MemoryManager()
        self.tools = ToolRegistry()

    async def run(self, prompt: str):
        plan = await self.planner.create_plan(prompt)

        results = []

        for step in plan["steps"]:
            result = await self.tools.execute(step, prompt)
            results.append(result)

        await self.memory.store(prompt)

        return {
            "plan": plan,
            "results": results,
        }
