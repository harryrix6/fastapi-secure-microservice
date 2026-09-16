import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis import Redis
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.auth import router as auth_router
from app.config import settings
from app.core.cache import cache
from app.core.rate_limiter import RateLimiter
from app.db.redis import close_redis_pool, get_redis, init_redis_pool

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis_pool()
    yield
    await close_redis_pool()


# Define OpenAPI tags for structured grouping
tags_metadata = [
    {
        "name": "Authentication",
        "description": "User account registration, JWT token generation, and identity endpoints.",
    },
    {
        "name": "Health & Diagnostics",
        "description": "System health checks, Redis connection validation, cache tests, and rate limiting verification.",
    },
]

# Markdown description for API header
api_description = """
### Secure FastAPI Microservice API

#### Security & Architecture Features
* **Authentication**: OAuth2 Password Bearer flow utilizing JWT access tokens and **Argon2** password hashing.
* **Rate Limiting**: Sliding window IP and user-based throttling backed by **Redis**.
* **Caching**: High-performance endpoint caching using asynchronous **Redis** pools.
* **Security Headers**: OWASP recommended HTTP response security headers enabled globally.
"""

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=api_description,
    version="1.0.0",
    openapi_tags=tags_metadata,
    swagger_ui_parameters={
        "docExpansion": "list",              # Expand tags by default, keep endpoints collapsed
        "filter": True,                      # Enable endpoint search bar
        "syntaxHighlight.theme": "monokai",  # Modern code syntax theme
        "tryItOutEnabled": True,             # Enable "Try it out" buttons by default
        "displayRequestDuration": True,      # Display request latency timing
    },
    lifespan=lifespan,
)


# ====================================================
# Global Exception Handlers
# ====================================================

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "An unexpected error occurred. Please try again later.",
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "status_code": exc.status_code,
            "message": exc.detail,
        },
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "message": "Validation Error",
            "errors": exc.errors(),
        },
    )


# ====================================================
# Middleware
# ====================================================

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    return response


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

# Register routers with tags
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])


# ====================================================
# Endpoints
# ====================================================

@app.get("/", tags=["Health & Diagnostics"], summary="Service Health Check")
async def root():
    """Verify microservice availability."""
    return {"status": "ok", "message": "Secure FastAPI Microservice is running"}


@app.get("/test-redis", tags=["Health & Diagnostics"], summary="Redis Ping Test")
async def test_redis(redis: Redis = Depends(get_redis)):
    """Test connection pool responsiveness to Redis."""
    pong = await redis.ping()
    return {"redis_status": "connected" if pong else "failed", "ping": pong}


@app.get("/test-cache", tags=["Health & Diagnostics"], summary="Response Cache Test")
@cache(ttl_seconds=30, prefix="test")
async def test_cache(request: Request):
    """Simulates a heavy 2-second database operation and caches the response for 30 seconds."""
    await asyncio.sleep(2)
    return {
        "timestamp": time.time(),
        "message": "Took 2 seconds on first hit. Serves instantly from Redis for next 30 seconds.",
    }


@app.get(
    "/test-rate-limit",
    tags=["Health & Diagnostics"],
    summary="Rate Limiter Test",
    dependencies=[Depends(RateLimiter(requests_limit=3, window_in_seconds=10))],
)
async def test_rate_limit():
    """Restricted to 3 requests per 10-second window."""
    return {"message": "Request successful!"}