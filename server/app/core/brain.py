from __future__ import annotations

from app.services.llm_service import ask_llm
from app.services.memory_service import MemoryService
from app.services.tool_service import ToolService


tool_service = ToolService()
memory_service = MemoryService()


def process_command(user_input: str, user_id: str = "default-user"):
    """Main command processor with tool routing + memory tracking."""
    memory_service.add_message(user_id, "user", user_input)

    action_result = tool_service.route(user_input)

    if action_result["action"] == "chat":
        response_text = ask_llm(
            user_input,
            system_prompt="You are Jarvis. Be concise and practical.",
        )
    else:
        response_text = action_result["message"]

    memory_service.add_message(user_id, "assistant", response_text)

    if action_result["action"] == "run_task":
        memory_service.add_task(user_id, title=user_input, status=action_result["status"])

    return {
        "response": response_text,
        "action": action_result["action"],
        "status": action_result["status"],
        "memory": {
            "recent_messages": memory_service.recent_messages(user_id),
            "recent_tasks": memory_service.recent_tasks(user_id),
        },
    }
