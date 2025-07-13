"""
Async database connection setup using SQLAlchemy Core.
"""

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from org_service.config import settings

# Convert URL to asyncpg-compatible format
DATABASE_URL = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")

# Create the global engine and session maker
engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)

# Declare the shared Base for models
Base = declarative_base()


async def init_db(engine: AsyncEngine) -> None:
    """
    Run this at application startup to initialize tables.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
