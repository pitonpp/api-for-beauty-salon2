from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.app.constants import ENCODING

BASE_DIR = Path(__file__).resolve().parents[3]

ENV_FILE = BASE_DIR / "infra" / ".env"


class Settings(BaseSettings):
    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_password: str
    postgres_name: str
    secret: str

    secret_key: str
    refresh_secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int

    model_config = SettingsConfigDict(
        env_file=ENV_FILE if ENV_FILE.exists() else None,
        env_file_encoding=ENCODING,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_name}"
        )


settings = Settings()
