from fastapi import FastAPI
from dotenv import load_dotenv
from pydantic import BaseModel
from app.core.brain import process_command

load_dotenv()

app = FastAPI()

class JarvisRequest(BaseModel):
    message: str

@app.post("/jarvis")
async def jarvis(req: JarvisRequest):
    result = process_command(req.message)
    return {"response": result}
