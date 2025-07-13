# tests/utils/db.py

from sqlalchemy.ext.asyncio import create_async_engine
from org_service.config import TEST_DB_URL


def get_test_engine():
    return create_async_engine(TEST_DB_URL, echo=False, future=True)
