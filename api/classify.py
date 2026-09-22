"""Vercel function for POST /api/classify."""

from fastapi import FastAPI

from backend.main import ClassifyRequest, classify as classify_backend

app = FastAPI(title="One Among Them Classification")


@app.post("/")
async def classify(request: ClassifyRequest):
    return await classify_backend(request)
