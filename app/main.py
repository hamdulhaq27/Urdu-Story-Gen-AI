from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.model import generate_story
from app.schemas import GenerateRequest
import os

app = FastAPI(title="Urdu Story Generator API")

# ── CORS ──────────────────────────────────────────────────────────────────────
# After Vercel deployment, set this env var on your server:
# ALLOWED_ORIGINS=https://your-app.vercel.app
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000"   # dev default
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Urdu Story Generator API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/generate")
def generate(request: GenerateRequest):
    story = generate_story(request.prefix, request.max_length)
    return {"generated_story": story}