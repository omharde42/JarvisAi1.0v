

from fastapi import FastAPI
from pydantic import BaseModel
from app.core.brain import JarvisBrain

app = FastAPI(title="Jarvis AI")

brain = JarvisBrain()

class RequestModel(BaseModel):
    message: str

@app.post("/jarvis")
async def jarvis_api(req: RequestModel):
    result = await brain.process(req.message)
    return result
