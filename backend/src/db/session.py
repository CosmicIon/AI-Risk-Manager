import logging
from collections.abc import AsyncGenerator
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.sql import text

from src.config import settings

logger = logging.getLogger(__name__)

# Create the async database engine
# - pool_size: Max number of permanent connections
# - max_overflow: Max number of temporary connections beyond pool_size
# - pool_pre_ping: Check connection validity before leasing from pool
async_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False,  # Set to True for SQL query logging during debugging
)

# Create the session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for obtaining a database session without tenant context.
    Only use this for operations that span multiple tenants or operate on tenant definitions themselves.
    """
    async with AsyncSessionLocal() as session:
        yield session


async def get_db_session_with_tenant(tenant_id: UUID) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for obtaining a database session WITH tenant context enforced.
    This injects the tenant_id into the Postgres session state for Row-Level Security (RLS).
    """
    async with AsyncSessionLocal() as session:
        # Enforce RLS at the database engine level
        await session.execute(text(f"SET app.current_tenant = '{tenant_id}'"))
        try:
            yield session
        finally:
            # Clear the context before returning to the pool
            await session.execute(text("RESET app.current_tenant"))
