 

from app.services.llm
service import generate_response
from app.planner.task_planner import decide_action

class JarvisBrain:

    def __init__(self):
        pass

    async def process(self, user_input: str):
        # Step 1: Decide what to do
        action = decide_action(user_input)

        # Step 2: If simple chat → LLM
        if action["type"] == "chat":
            response = await generate_response(user_input)
            return {"response": response}

        # Step 3: If tool needed
        elif action["type"] == "tool":
            return {
                "response": f"Executing tool: {action['tool']}",
                "action": action
            }

        # Step 4: fallback
        return {"response": "I didn't understand."}
