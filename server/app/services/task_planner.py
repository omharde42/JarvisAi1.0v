"""
Task Planner Service
Multi-step task planning and execution orchestration
"""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService
from app.db.models import Task, TaskStatus, TaskPriority

logger = logging.getLogger(__name__)


class TaskStep:
    """Represents a single step in a task execution plan"""
    
    def __init__(
        self,
        step_id: int,
        description: str,
        tool: str,
        params: Dict[str, Any],
        depends_on: Optional[List[int]] = None,
        is_parallel: bool = False,
    ):
        self.step_id = step_id
        self.description = description
        self.tool = tool
        self.params = params
        self.depends_on = depends_on or []
        self.is_parallel = is_parallel
        self.status = "pending"
        self.result = None
        self.error = None
        self.executed_at = None


class TaskPlanner:
    """
    Task planner using LLM reasoning for multi-step execution
    
    Features:
    - Decompose complex tasks into steps
    - Generate execution plans with dependencies
    - Handle parallel execution
    - Support for tool chaining
    - Context-aware planning using memory
    """
    
    def __init__(self, llm_service: LLMService, memory_service: MemoryService):
        self.llm = llm_service
        self.memory = memory_service
        self.logger = logger
    
    async def plan_task(
        self,
        user_id: str,
        task_goal: str,
        available_tools: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a multi-step execution plan for a complex task
        
        Args:
            user_id: User making the request
            task_goal: High-level goal/description
            available_tools: List of available tool names
            context: Additional context for planning
        
        Returns:
            Plan with steps, dependencies, and execution order
        """
        
        self.logger.info(f"Planning task: {task_goal}")
        
        # Retrieve relevant memory context
        relevant_context = await self.memory.retrieve_relevant_context(
            user_id, task_goal
        )
        
        # Build prompt for LLM
        planning_prompt = self._build_planning_prompt(
            task_goal=task_goal,
            available_tools=available_tools,
            context=context or {},
            memory_context=relevant_context,
        )
        
        # Get LLM to generate plan
        try:
            response = await self.llm.chat_completion(
                messages=[
                    {"role": "system", "content": "You are an expert task planner."},
                    {"role": "user", "content": planning_prompt},
                ],
                temperature=0.7,
            )
            
            plan_text = response.get("content", "")
            plan = self._parse_plan(plan_text)
            
            self.logger.info(f"Generated plan with {len(plan['steps'])} steps")
            return plan
            
        except Exception as e:
            self.logger.error(f"Failed to plan task: {str(e)}")
            raise
    
    async def execute_plan(
        self,
        user_id: str,
        task_id: str,
        plan: Dict[str, Any],
        tool_executor: Any,  # Will receive tool executor from orchestrator
    ) -> Dict[str, Any]:
        """
        Execute a task plan step by step
        
        Args:
            user_id: User executing the task
            task_id: Task ID being executed
            plan: Execution plan with steps
            tool_executor: Tool executor to run individual steps
        
        Returns:
            Execution results with step outputs
        """
        
        self.logger.info(f"Executing plan for task {task_id}")
        
        results = {
            "task_id": task_id,
            "steps_executed": 0,
            "steps_failed": 0,
            "step_results": [],
            "final_result": None,
            "errors": [],
        }
        
        steps = plan.get("steps", [])
        executed_steps = {}
        
        for i, step_data in enumerate(steps):
            try:
                step = TaskStep(
                    step_id=step_data.get("id", i),
                    description=step_data.get("description", ""),
                    tool=step_data.get("tool", ""),
                    params=step_data.get("params", {}),
                    depends_on=step_data.get("depends_on", []),
                    is_parallel=step_data.get("is_parallel", False),
                )
                
                # Check dependencies
                if not self._dependencies_met(step, executed_steps):
                    self.logger.warning(f"Skipping step {step.step_id} - dependencies not met")
                    continue
                
                # Execute step
                self.logger.info(f"Executing step {step.step_id}: {step.description}")
                
                result = await tool_executor.execute(
                    tool_name=step.tool,
                    params=step.params,
                    context={"task_id": task_id, "user_id": user_id},
                )
                
                step.status = "completed"
                step.result = result
                step.executed_at = datetime.utcnow().isoformat()
                executed_steps[step.step_id] = step
                
                results["steps_executed"] += 1
                results["step_results"].append({
                    "step_id": step.step_id,
                    "status": "completed",
                    "result": result,
                })
                
            except Exception as e:
                self.logger.error(f"Step {step.step_id} failed: {str(e)}")
                results["steps_failed"] += 1
                results["errors"].append({
                    "step_id": step.step_id,
                    "error": str(e),
                })
                
                # Decide whether to continue or abort
                if step_data.get("critical", False):
                    self.logger.error("Critical step failed, aborting execution")
                    break
        
        results["final_result"] = self._synthesize_results(results["step_results"])
        
        return results
    
    def _build_planning_prompt(self, task_goal: str, available_tools: List[str], context: Dict, memory_context: str) -> str:
        """
        Build a prompt for the LLM to generate a task plan
        """
        
        tools_str = "\n".join([f"- {tool}" for tool in available_tools])
        
        prompt = f"""
You are a task planning expert. Break down the following goal into concrete steps.

GOAL: {task_goal}

AVAILABLE TOOLS:
{tools_str}

RELEVANT CONTEXT FROM MEMORY:
{memory_context}

Generate a JSON execution plan with the following structure:
{{
  "steps": [
    {{
      "id": 1,
      "description": "Step description",
      "tool": "tool_name",
      "params": {{}},
      "depends_on": [],
      "is_parallel": false,
      "critical": true
    }}
  ],
  "estimated_duration_seconds": 60,
  "reasoning": "Explanation of the plan"
}}
"""
        return prompt
    
    def _parse_plan(self, plan_text: str) -> Dict[str, Any]:
        """
        Parse LLM-generated plan from text
        """
        try:
            # Try to extract JSON
            json_start = plan_text.find("{")
            json_end = plan_text.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = plan_text[json_start:json_end]
                plan = json.loads(json_str)
                return plan
            
            # Fallback
            return {"steps": [], "reasoning": plan_text}
            
        except Exception as e:
            self.logger.error(f"Failed to parse plan: {str(e)}")
            return {"steps": [], "reasoning": plan_text, "parse_error": str(e)}
    
    def _dependencies_met(self, step: TaskStep, executed_steps: Dict) -> bool:
        """
        Check if all dependencies for a step are met
        """
        for dep_id in step.depends_on:
            if dep_id not in executed_steps or executed_steps[dep_id].status != "completed":
                return False
        return True
    
    def _synthesize_results(self, step_results: List[Dict]) -> str:
        """
        Synthesize individual step results into final output
        """
        if not step_results:
            return "No steps executed"
        
        synthesis = "Task completed with the following results:\n"
        for result in step_results:
            synthesis += f"\nStep {result['step_id']}: {result['result']}\n"
        
        return synthesis
