import os
from collections.abc import AsyncIterator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.db import Base

TEST_DATABASE_URL = os.getenv(
    'TEST_DATABASE_URL',
    'postgresql+asyncpg://test:test@localhost:5433/test_db',
)


@pytest.fixture(scope='session')
async def async_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def session(async_engine) -> AsyncIterator[AsyncSession]:
    async with AsyncSession(
        bind=async_engine,
        expire_on_commit=False,
    ) as session:
        yield session


TABLES_TO_CLEAN = [
    'appointment',
    'masterservice',
    'master',
    'service',
    'refreshtoken',
    '"user"',
]


@pytest.fixture(autouse=True)
async def _clean_db(async_engine):
    yield
    async with async_engine.begin() as conn:
        for table in TABLES_TO_CLEAN:
            await conn.execute(text(f'TRUNCATE TABLE {table} CASCADE'))
