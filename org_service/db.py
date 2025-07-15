"""
Async database connection setup using SQLAlchemy Core.
"""

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from org_service.config import settings

# Convert URL to asyncpg-compatible format
DATABASE_URL = settings.get_async_database_url()

# Create the global engine and session maker
engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)

# Declare the shared Base for models
Base = declarative_base()


def get_sync_url_for_alembic() -> str:
    """Returns sync-style DB URL for use in Alembic config."""
    return settings.get_sync_database_url()
