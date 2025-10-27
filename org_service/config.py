"""
Configuration and logging setup for org-service.
Phase 1: Minimal Google OAuth + JWT (no database).
"""

import logging
import sys

from pydantic_settings import BaseSettings, SettingsConfigDict
from pythonjsonlogger import jsonlogger


# Structured JSON logging configuration
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""

    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict) -> None:  # type: ignore[override]
        """Add custom fields to log records."""
        super().add_fields(log_record, record, message_dict)
        log_record["service"] = "org-service"
        log_record["level"] = record.levelname


# Configure JSON logging
log_handler = logging.StreamHandler(sys.stdout)
formatter = CustomJsonFormatter(
    "%(asctime)s %(level)s %(name)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log_handler.setFormatter(formatter)

logger = logging.getLogger("org_service")
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)
logger.propagate = False


# Settings configuration
class Settings(BaseSettings):
    """Application settings loaded from .env or environment variables."""

    # Google OAuth
    google_client_id: str
    google_client_secret: str
    google_oauth_redirect_uri: str

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiry_seconds: int = 604800  # 7 days for Phase 1

    # Phase 1: Hardcoded org ID (no database)
    hardcoded_org_id: str = "11111111-1111-1111-1111-111111111111"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()  # type: ignore[call-arg]
