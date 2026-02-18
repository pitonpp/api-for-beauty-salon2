from sqlalchemy import Column, Integer
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    mapped_column,
    Mapped,
    declared_attr,
)

from app.core.config import settings


class Base(DeclarativeBase):
    pass


class CommonBaseMixin:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id: Mapped[int] = mapped_column(Integer, primary_key=True)


engine = create_async_engine(settings.database_url)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session():
    async with AsyncSessionLocal() as async_session:
        yield async_session
