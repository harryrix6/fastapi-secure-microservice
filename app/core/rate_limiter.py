from fastapi import HTTPException, Request, status, Depends
from redis.asyncio import Redis
from app.db.redis import get_redis

class RateLimiter:
    def __init__(self, requests_limit: int, window_in_seconds: int):
        self.requests_limit = requests_limit
        self.window_in_seconds = window_in_seconds

    async def __call__(
        self,
        request: Request,
        redis: Redis = Depends(get_redis)
    ) -> None:
        # Determine client identity (authenticated user ID if present, else client IP)
        client_ip = request.client.host if request.client else "unknown"
        user_id = getattr(request.state, "user_id", None)
        identifier = f"user:{user_id}" if user_id else f"ip:{client_ip}"

        # Redis key format: rate_limit:<path>:<identifier>
        key = f"rate_limit:{request.url.path}:{identifier}"

        # Atomic increment in Redis
        current_requests = await redis.incr(key)

        # On the first request in this window, set the expiration key
        if current_requests == 1:
            await redis.expire(key, self.window_in_seconds)

        # Check limit breach
        if current_requests > self.requests_limit:
            ttl = await redis.ttl(key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": str(max(ttl, 1))},
            )