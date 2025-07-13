"""
User model representing a person tied to an account.
Supports both OAuth and manual login.
"""

import uuid
from sqlalchemy import Column, String, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from .base import Base


class User(Base):
    """Represents an authenticated user belonging to an account."""

    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(
        UUID(as_uuid=True), ForeignKey("accounts.account_id"), nullable=False
    )
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    google_sub = Column(String, unique=True, nullable=True)
    # password_hash = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
