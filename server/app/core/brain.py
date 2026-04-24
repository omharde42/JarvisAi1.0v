from app.services.llm_service import ask_llm

def process_command(user_input: str):
    
    # Step 1: Understand intent
    intent = ask_llm(f"Understand this command and classify it: {user_input}")
    
    # Step 2: Simple decision logic
    if "open" in user_input.lower():
        return "Opening application (not implemented yet)"
    
    elif "code" in user_input.lower():
        return "Generating code (next step)"
    
    else:
        return ask_llm(user_input)
