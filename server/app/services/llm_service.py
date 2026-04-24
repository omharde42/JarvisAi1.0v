"""LLM service helpers with safe fallbacks."""

from __future__ import annotations

import importlib
import os
from typing import Any, Dict, Optional


def _load_module(name: str):
    """Load a module if installed, else return None."""
    spec = importlib.util.find_spec(name)
    if spec is None:
        return None
    return importlib.import_module(name)


def ask_llm(prompt: str, *, system_prompt: Optional[str] = None) -> str:
    """
    Best-effort LLM call.

    Priority:
    1) OpenAI (if SDK installed + OPENAI_API_KEY present)
    2) Deterministic local fallback
    """
    openai = _load_module("openai")
    api_key = os.getenv("OPENAI_API_KEY")

    if openai is not None and api_key:
        try:
            client = openai.OpenAI(api_key=api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=messages,
                temperature=0.2,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception:
            # Continue to local fallback.
            pass

    # Local fallback keeps phase 1 usable without external provider setup.
    return f"[local-fallback] I understood: {prompt}"


def provider_status() -> Dict[str, Any]:
    """Expose simple provider diagnostics for health checks."""
    return {
        "openai_sdk_installed": _load_module("openai") is not None,
        "openai_api_key_set": bool(os.getenv("OPENAI_API_KEY")),
    }
