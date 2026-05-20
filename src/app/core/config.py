from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.constants import ENCODING

BASE_DIR = Path(__file__).resolve().parents[3]

ENV_FILE = BASE_DIR / "infra" / ".env"


class Settings(BaseSettings):
    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_password: str
    postgres_db: str
    secret: str

    secret_key: str
    refresh_secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int

    first_superuser_username: str
    first_superuser_first_name: str
    first_superuser_last_name: str
    first_superuser_password: str
    first_superuser_phonenumber: str
    first_user_username: str
    first_user_first_name: str
    first_user_last_name: str
    first_user_password: str
    first_user_phonenumber: str
    first_master_username: str
    first_master_first_name: str
    first_master_last_name: str
    first_master_password: str
    first_master_phonenumber: str

    broker_url: str

    model_config = SettingsConfigDict(
        env_file=ENV_FILE if ENV_FILE.exists() else None,
        env_file_encoding=ENCODING,
        extra="ignore",
    )

    @property
    def async_database_url(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_database_url(self) -> str:
        return (
            f"postgresql://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
