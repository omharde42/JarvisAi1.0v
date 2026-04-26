# server/app/planner/task_planner.py

def decide_action(user_input: str):
    text = user_input.lower()

    # 🔥 Simple rules (we upgrade later with AI)
    
    if "open" in text:
        return {"type": "tool", "tool": "open_app", "input": text}

    elif "code" in text:
        return {"type": "tool", "tool": "code_generator", "input": text}

    elif "search" in text or "google" in text:
        return {"type": "tool", "tool": "browser_search", "input": text}

    else:
        return {"type": "chat"}
