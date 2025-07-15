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

    def get_sync_database_url(self, test: bool = False) -> str:
        url = self.database_url
        return url + "_test" if test else url

    def get_async_database_url(self, test: bool = False) -> str:
        return self.get_sync_database_url(test).replace(
            "postgresql://", "postgresql+asyncpg://"
        )

    class Config:
        env_file = ".env"


settings = Settings()
