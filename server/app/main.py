from fastapi import FastAPI
from dotenv import load_dotenv
from pydantic import BaseModel

from app.core.brain import process_command

load_dotenv()

app = FastAPI()


class JarvisRequest(BaseModel):
    message: str
    user_id: str = "default-user"


@app.post("/jarvis")
async def jarvis(req: JarvisRequest):
    return process_command(req.message, user_id=req.user_id)
