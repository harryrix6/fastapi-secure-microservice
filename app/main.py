from fastapi import FastAPI
from app.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-ready REST API with Auth and Rate Limiting",
    version="1.0.0",
)

@app.get("/")
async def root():
    return {"message": "API is online and running cleanly"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}