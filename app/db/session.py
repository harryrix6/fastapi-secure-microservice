from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# Create async engine with pool configuration
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Set to False in production to disable SQL log output
    future=True,
    pool_pre_ping=True,  # Verifies connectivity before borrowing connections
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for SQLAlchemy ORM models
class Base(DeclarativeBase):
    pass

# Dependency to provide async DB sessions to FastAPI endpoints
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()