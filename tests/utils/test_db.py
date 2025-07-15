from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from org_service.config import settings

# Create async engine for test DB
_test_engine = create_async_engine(
    settings.get_async_database_url(test=True), echo=False, future=True
)
_test_sessionmaker = async_sessionmaker(
    bind=_test_engine, class_=AsyncSession, expire_on_commit=False
)


def get_test_engine():
    return _test_engine


@asynccontextmanager
async def get_test_session() -> AsyncGenerator[AsyncSession, None]:
    session = _test_sessionmaker()
    try:
        yield session
    finally:
        await session.close()
