from datetime import datetime

from sqlalchemy import DateTime, Integer, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
)

from app.core.config import settings


class Base(DeclarativeBase):
    """Базовый класс для всех SQLAlchemy моделей."""


class CommonBaseMixin:
    """Mixin с общими полями: id, created_at, и авто-именованием таблицы."""
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )


engine = create_async_engine(settings.async_database_url)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session():
    """Генератор асинхронной сессии БД с обработкой ошибок."""
    async with AsyncSessionLocal() as async_session:
        try:
            yield async_session
        except SQLAlchemyError:
            await async_session.rollback()
            raise
