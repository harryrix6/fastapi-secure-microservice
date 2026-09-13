from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)

from app.config import settings
from app.main import app
from app.db.session import Base
from app.api.deps import get_db
from app.db.redis import init_redis_pool, close_redis_pool, pool as redis_pool


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_environment():
    """Sets up fresh engine tables and Redis pool per test loop to prevent loop mismatch errors."""
    # Create engine within current loop
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    # Initialize DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Initialize Redis Pool
    await init_redis_pool()
    redis_client = Redis(connection_pool=redis_pool)
    await redis_client.flushdb()

    yield {
        "engine": engine,
        "session_factory": session_factory,
        "redis": redis_client,
    }

    # Teardown
    await redis_client.flushdb()
    await redis_client.aclose()
    await close_redis_pool()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def db_session(
    setup_test_environment: dict,
) -> AsyncGenerator[AsyncSession, None]:
    """Yields an isolated transactional DB session."""
    session_factory = setup_test_environment["session_factory"]
    async with session_factory() as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provides an AsyncClient bound to the FastAPI app with DB dependency override."""

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()