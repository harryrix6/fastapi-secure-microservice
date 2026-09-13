from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request

from redis import Redis

from app.config import settings
from app.api.auth import router as auth_router

from contextlib import asynccontextmanager
from app.db.redis import init_redis_pool, close_redis_pool, get_redis

from app.core.rate_limiter import RateLimiter
from app.core.cache import cache

import asyncio
import time


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Redis pool
    await init_redis_pool()
    yield
    # Shutdown: Close Redis pool cleanly
    await close_redis_pool()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-ready REST API with Authentication and Rate Limiting",
    version="1.0.0",
    lifespan=lifespan,
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

@app.get("/test-redis")
async def test_redis(redis: Redis = Depends(get_redis)):
    pong = await redis.ping()
    return {"redis_status": "connected" if pong else "failed", "ping": pong}

@app.get("/test-cache", tags=["health"])
@cache(ttl_seconds=30, prefix="test")
async def test_cache(request: Request):
    # Simulate a heavy DB or 3rd party calculation (2-sec delay)
    await asyncio.sleep(2)
    return {
        "timestamp": time.time(),
        "message": "Took 2 seconds. Serves instantly from Redis for next 30 seconds."
    }

@app.get("/test-rate-limit", dependencies=[Depends(RateLimiter(requests_limit=3, window_in_seconds=10))])
async def test_rate_limit():
    return {"message": "Request successful!"}
