import logging
from typing import AsyncGenerator, Optional
from redis.asyncio import ConnectionPool, Redis
from app.config import settings

logger = logging.getLogger("uvicorn")

# Global connection pool instance
pool: Optional[ConnectionPool] = None

async def init_redis_pool() -> None:
    """Initialize the global Redis connection pool on app startup."""
    global pool
    try:
        pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            decode_responses=True,  # Automatically decodes bytes to strings
            max_connections=10,
        )
        # Test connection
        client = Redis(connection_pool=pool)
        await client.ping()
        print(">>> [REDIS] Connected successfully to Redis server!")
    except Exception as e:
        print(f">>> [REDIS ERROR] Failed to connect: {e}")
        raise e

async def close_redis_pool() -> None:
    """Close the global Redis connection pool on app shutdown."""
    global pool
    if pool:
        await pool.disconnect()
        logger.info("Redis connection pool closed.")

def get_redis_pool() -> Optional[ConnectionPool]:
    """Dynamically fetch the current connection pool instance."""
    return pool

async def get_redis() -> AsyncGenerator[Redis, None]:
    """Dependency that yields a Redis client from the connection pool."""
    if pool is None:
        raise RuntimeError("Redis connection pool is not initialized.")

    client = Redis(connection_pool=pool)
    try:
        yield client
    finally:
        await client.aclose()