"""
Configuration loader for environment variables using Pydantic.
"""

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from .env or environment variables."""

    database_url: str

    google_client_id: str
    google_client_secret: str
    google_oauth_redirect_uri: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiry_seconds: int = 3600

    class Config:
        env_file = ".env"

    def get_async_database_url(self) -> str:
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://")

    def get_test_database_url(self) -> str:
        return self.database_url + "_test"

    def get_async_test_database_url(self) -> str:
        return self.get_test_database_url().replace(
            "postgresql://", "postgresql+asyncpg://"
        )


settings = Settings()

# Legacy fallback for test DB usage
TEST_DB_URL = settings.get_async_test_database_url()
