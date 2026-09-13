import functools
import json
import logging
from typing import Any, Callable, Optional
from fastapi import Request
from redis.asyncio import Redis
from app.db.redis import get_redis_pool

logger = logging.getLogger("uvicorn")


class CacheService:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def get(self, key: str) -> Optional[Any]:
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        serialized = json.dumps(value, default=str)
        await self.redis.set(key, serialized, ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        await self.redis.delete(key)

    async def clear_pattern(self, pattern: str) -> None:
        async for key in self.redis.scan_iter(match=pattern):
            await self.redis.delete(key)


def cache(ttl_seconds: int = 60, prefix: str = "cache"):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 1. Search kwargs and args directly for Request
            request: Optional[Request] = kwargs.get("request")
            if not request:
                for arg in list(args) + list(kwargs.values()):
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request:
                logger.warning("[CACHE DEBUG] Request object NOT found in arguments! Bypassing cache...")
                return await func(*args, **kwargs)

            # 2. Dynamically fetch active connection pool
            pool = get_redis_pool()
            if pool is None:
                logger.warning("[CACHE DEBUG] Redis pool is None! Bypassing cache...")
                return await func(*args, **kwargs)

            query_str = f"?{request.query_params}" if request.query_params else ""
            cache_key = f"{prefix}:{request.url.path}{query_str}"

            async with Redis(connection_pool=pool) as redis:
                # 3. Check Redis cache hit
                cached_data = await redis.get(cache_key)
                if cached_data:
                    logger.info(f"[CACHE HIT] Serving key '{cache_key}' directly from Redis!")
                    return json.loads(cached_data)

                # 4. Cache miss: execute function & store
                logger.info(f"[CACHE MISS] Executing handler for key '{cache_key}'...")
                result = await func(*args, **kwargs)
                serialized_result = json.dumps(result, default=str)
                await redis.set(cache_key, serialized_result, ex=ttl_seconds)
                logger.info(f"[CACHE STORED] Saved result to key '{cache_key}' with TTL {ttl_seconds}s")

                return result

        return wrapper
    return decorator