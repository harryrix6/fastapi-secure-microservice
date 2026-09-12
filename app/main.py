from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.auth import router as auth_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-ready REST API with Authentication and Rate Limiting",
    version="1.0.0",
)

# Define allowed origins
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Register auth router
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

@app.get("/", tags=["health"])
async def root():
    return {"status": "ok", "message": "Secure FastAPI Microservice is running"}