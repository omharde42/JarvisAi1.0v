from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Jarvis is running"}

@app.post("/jarvis")
async def jarvis(query: dict):
    user_input = query.get("message")
    
    response = ask_llm(user_input)
    
    return {"response": response}
