"""Async database engine and session factory."""
import sys

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from app.config import settings

# Use NullPool during pytest to avoid asyncpg connection teardown issues
# on Python 3.14 + Windows (ProactorEventLoop). In production, use the
# standard connection pool for performance.
_is_testing = "pytest" in sys.modules

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "local",
    **({"poolclass": NullPool} if _is_testing else {
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 10,
    }),
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """FastAPI dependency: yields an async DB session, auto-closes."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

