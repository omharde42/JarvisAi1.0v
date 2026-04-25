"""Phase 2 tool router: code, browser/open, task actions."""

from __future__ import annotations

from typing import Dict, Any


class ToolService:
    def route(self, user_input: str) -> Dict[str, Any]:
        text = user_input.lower()

        if any(k in text for k in ["code", "write", "generate", "python", "script"]):
            return {
                "action": "write_code",
                "status": "ready",
                "message": "Code tool selected. Provide your coding requirement.",
                "data": {"tool": "code"},
            }

        if any(k in text for k in ["browser", "open", "website", "url"]):
            return {
                "action": "open_browser",
                "status": "ready",
                "message": "Browser tool selected. Share the URL to open.",
                "data": {"tool": "browser"},
            }

        if any(k in text for k in ["task", "run", "execute", "do this"]):
            return {
                "action": "run_task",
                "status": "queued",
                "message": "Task tool selected. Task captured and queued.",
                "data": {"tool": "task-runner"},
            }

        return {
            "action": "chat",
            "status": "fallback",
            "message": "No direct tool matched; using chat mode.",
            "data": {"tool": "llm"},
        }
