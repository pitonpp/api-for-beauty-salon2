from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_host: str
    db_port: int = 5432
    db_user: str
    db_password: str
    db_name: str
    secret: str

    model_config = SettingsConfigDict(env_file=".env")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
