from typing import Dict, Any, List


class TaskPlanner:
    """
    Breaks user requests into executable steps
    """

    async def create_plan(self, prompt: str) -> Dict[str, Any]:
        steps: List[str] = []

        prompt_lower = prompt.lower()

        if "search" in prompt_lower:
            steps.append("web_search")

        if "calculate" in prompt_lower:
            steps.append("calculator")

        if "remember" in prompt_lower:
            steps.append("store_memory")

        if not steps:
            steps.append("general_response")

        return {
            "goal": prompt,
            "steps": steps,
            "status": "planned"
        }
