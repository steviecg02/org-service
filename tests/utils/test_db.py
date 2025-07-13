from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from org_service.config import settings

# Use test DB URL derived from main DB
_test_db_url = (
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://") + "_test"
)

_test_engine = create_async_engine(_test_db_url, future=True, echo=False)
_test_sessionmaker = async_sessionmaker(
    bind=_test_engine, class_=AsyncSession, expire_on_commit=False
)

if not settings.database_url.endswith("_test"):
    raise RuntimeError("Test DB loaded in non-test environment!")


def get_test_engine():
    return _test_engine


async def get_test_session() -> AsyncSession:
    return _test_sessionmaker()
