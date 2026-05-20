import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.db import Base


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
async def async_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def session(async_engine):
    connection = await async_engine.connect()
    transaction = await connection.begin()

    async_session = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as s:
        yield s

    await transaction.rollback()
    await connection.close()
