"""
Agent Planner - Task Decomposition and Planning
Breaks down complex goals into actionable steps
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from app.core.llm import LLMProvider
from app.core.exceptions import PlanningError

logger = logging.getLogger(__name__)


class PlanStep:
    """
    Represents a single step in an execution plan
    """

    def __init__(
        self,
        step_id: int,
        description: str,
        action_type: str,  # think, act, observe, decide
        tool: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        depends_on: Optional[List[int]] = None,
    ):
        self.step_id = step_id
        self.description = description
        self.action_type = action_type
        self.tool = tool
        self.parameters = parameters or {}
        self.depends_on = depends_on or []
        self.status = "pending"
        self.result = None
        self.error = None
        self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "step_id": self.step_id,
            "description": self.description,
            "action_type": self.action_type,
            "tool": self.tool,
            "parameters": self.parameters,
            "depends_on": self.depends_on,
            "status": self.status,
            "result": self.result,
            "error": self.error,
        }


class Plan:
    """
    Execution plan containing multiple steps
    """

    def __init__(self, goal: str, reasoning: str):
        self.goal = goal
        self.reasoning = reasoning
        self.steps: List[PlanStep] = []
        self.created_at = datetime.utcnow()
        self.status = "created"

    def add_step(self, step: PlanStep) -> None:
        """Add step to plan"""
        self.steps.append(step)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "goal": self.goal,
            "reasoning": self.reasoning,
            "steps": [step.to_dict() for step in self.steps],
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }


class AgentPlanner:
    """
    AI Agent Planner
    Uses LLM to create execution plans for complex goals

    Features:
    - Goal decomposition
    - Multi-step planning
    - Dependency resolution
    - Chain-of-thought reasoning
    """

    def __init__(self, llm_provider: LLMProvider):
        """
        Initialize planner with LLM provider
        """
        self.llm = llm_provider
        logger.info("✅ Agent Planner initialized")

    async def create_plan(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
        available_tools: Optional[List[str]] = None,
    ) -> Plan:
        """
        Create execution plan for a goal

        Args:
            goal: The goal to achieve
            context: Additional context
            available_tools: List of available tools

        Returns:
            Execution plan
        """
        try:
            logger.info(f"📋 Creating plan for goal: {goal}")

            # Build planning prompt
            prompt = self._build_planning_prompt(
                goal=goal,
                context=context or {},
                available_tools=available_tools or [],
            )

            # Get plan from LLM
            response = await self.llm.generate(
                prompt=prompt,
                temperature=0.5,  # Lower temperature for more deterministic planning
                max_tokens=2000,
            )

            if not response:
                raise PlanningError("Failed to generate plan from LLM")

            # Parse plan
            plan = self._parse_plan(goal, response)

            logger.info(f"✅ Plan created with {len(plan.steps)} steps")
            return plan

        except Exception as e:
            logger.error(f"Planning failed: {str(e)}", exc_info=True)
            raise PlanningError(f"Failed to create plan: {str(e)}")

    def _build_planning_prompt(self, goal: str, context: Dict[str, Any], available_tools: List[str]) -> str:
        """
        Build prompt for LLM to create a plan
        """
        tools_str = "\n".join([f"- {tool}" for tool in available_tools]) if available_tools else "- chat (default)"

        prompt = f"""
You are an expert AI planner. Create a detailed execution plan to achieve the following goal.

GOAL: {goal}

CONTEXT: {json.dumps(context, indent=2)}

AVAILABLE TOOLS:
{tools_str}

CREATE A JSON PLAN with this structure:
{{
  "reasoning": "Why this plan will work",
  "steps": [
    {{
      "step_id": 1,
      "description": "What to do",
      "action_type": "think|act|observe|decide",
      "tool": "tool_name or null",
      "parameters": {{}},
      "depends_on": []
    }}
  ]
}}

Be specific and actionable. Each step should lead toward the goal.
"""
        return prompt

    def _parse_plan(self, goal: str, response: str) -> Plan:
        """
        Parse LLM response into a Plan object
        """
        try:
            # Extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                plan_data = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")

            # Create plan object
            plan = Plan(
                goal=goal,
                reasoning=plan_data.get("reasoning", "No reasoning provided"),
            )

            # Add steps
            for step_data in plan_data.get("steps", []):
                step = PlanStep(
                    step_id=step_data.get("step_id", len(plan.steps) + 1),
                    description=step_data.get("description", ""),
                    action_type=step_data.get("action_type", "act"),
                    tool=step_data.get("tool"),
                    parameters=step_data.get("parameters", {}),
                    depends_on=step_data.get("depends_on", []),
                )
                plan.add_step(step)

            return plan

        except Exception as e:
            logger.error(f"Failed to parse plan: {str(e)}")
            # Return simple fallback plan
            plan = Plan(goal=goal, reasoning="Fallback plan")
            step = PlanStep(
                step_id=1,
                description=goal,
                action_type="act",
            )
            plan.add_step(step)
            return plan
