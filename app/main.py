from fastapi import FastAPI
from pydantic import BaseModel
from app.model import generate_story

app = FastAPI(title="Urdu Story Generator API")

class GenerateRequest(BaseModel):
    prefix: str
    max_length: int = 100

@app.get("/")
def root():
    return {"message": "Urdu Story Generator API is running"}

@app.post("/generate")
def generate(request: GenerateRequest):
    story = generate_story(request.prefix, request.max_length)
    return {"generated_story": story}
