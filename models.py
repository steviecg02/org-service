"""
Database models for users and accounts.
"""

import uuid
from sqlalchemy import Column, String, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Account(Base):
    """Represents an organization or tenant account."""

    __tablename__ = "accounts"

    account_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, server_default=func.now())


class User(Base):
    """Represents an authenticated user belonging to an account."""

    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(
        UUID(as_uuid=True), ForeignKey("accounts.account_id"), nullable=False
    )
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    google_sub = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
