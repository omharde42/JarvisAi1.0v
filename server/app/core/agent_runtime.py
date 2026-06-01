"""
Agent Runtime - Autonomous Execution Engine
Orchestrates planner, memory, and tool execution
"""

import logging
from typing import Any, Dict, Optional

from app.services.task_planner import TaskPlanner
from app.services.memory_manager import MemoryManager
from app.services.tool_executor import ToolExecutor
from app.core.config import settings

logger = logging.getLogger(__name__)


class AgentRuntime:
    """
    Main autonomous execution runtime

    Orchestrates:
    - Task planning (breaking down goals into steps)
    - Tool execution (running individual steps)
    - Memory management (storing context and results)
    """

    def __init__(self):
        """Initialize agent runtime with all subsystems"""
        try:
            self.planner = TaskPlanner(None, None)  # Will be injected by brain
            self.memory = MemoryManager(data_dir="data/memory")
            self.tool_executor = ToolExecutor(timeout=settings.TOOLS_TIMEOUT)
            logger.info("✅ Agent Runtime initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Agent Runtime: {str(e)}", exc_info=True)
            raise

    async def run(
        self,
        prompt: str,
        user_id: str = "default_user",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute agent pipeline

        Args:
            prompt: User request
            user_id: User identifier
            context: Optional execution context

        Returns:
            Execution results with plan and step outputs
        """
        try:
            logger.info(f"🚀 Agent executing prompt: {prompt[:100]}...")

            # Step 1: Store initial request in memory
            await self.memory.store_memory(
                user_id=user_id,
                content=f"User request: {prompt}",
                memory_type="conversation",
                tags=["request"],
            )

            # Step 2: Create execution plan
            # Note: Planner needs to be properly initialized with LLM service
            # For now, return basic plan
            plan = {
                "goal": prompt,
                "steps": [
                    {
                        "id": 1,
                        "description": "Analyze request",
                        "tool": "echo",
                        "params": {"message": f"Processing: {prompt}"},
                    }
                ],
                "status": "planned",
            }

            logger.info(f"📋 Plan created with {len(plan.get('steps', []))} steps")

            # Step 3: Execute plan steps
            results = []
            for step in plan.get("steps", []):
                try:
                    logger.info(f"Executing step {step.get('id')}: {step.get('description')}")

                    # Execute tool
                    result = await self.tool_executor.execute(
                        tool_name=step.get("tool", "echo"),
                        parameters=step.get("params", {}),
                    )

                    results.append(result)

                    # Store step result in memory
                    await self.memory.store_memory(
                        user_id=user_id,
                        content=f"Step {step.get('id')} result: {result}",
                        memory_type="conversation",
                        tags=["step_result"],
                    )

                except Exception as e:
                    logger.error(f"Step {step.get('id')} failed: {str(e)}")
                    results.append({"error": str(e)})

            logger.info("✅ Agent execution complete")

            return {
                "success": True,
                "plan": plan,
                "results": results,
                "user_id": user_id,
            }

        except Exception as e:
            logger.error(f"❌ Agent execution failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "plan": None,
                "results": [],
                "error": str(e),
            }
