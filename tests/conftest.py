from typing import AsyncGenerator

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from redis.asyncio import Redis, ConnectionPool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)

from app.config import settings
from app.main import app
from app.db.session import Base
import app.db.redis as redis_module
from app.db.redis import get_redis
from app.api.deps import get_db


@pytest_asyncio.fixture(scope="function", autouse=True)
async def prepare_database():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def redis_client() -> AsyncGenerator[Redis, None]:
    test_pool = ConnectionPool.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )

    old_pool = getattr(redis_module, "pool", None)
    redis_module.pool = test_pool

    client = Redis(connection_pool=test_pool)

    await client.flushdb()

    yield client

    await client.flushdb()
    await client.aclose()
    await test_pool.disconnect()

    redis_module.pool = old_pool


@pytest_asyncio.fixture(scope="function")
async def db_session(
    prepare_database,
) -> AsyncGenerator[AsyncSession, None]:

    engine = prepare_database

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(
    db_session: AsyncSession,
    redis_client: Redis,
) -> AsyncGenerator[AsyncClient, None]:

    async def _override_get_db():
        yield db_session

    async def _override_get_redis():
        yield redis_client

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_redis] = _override_get_redis

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()