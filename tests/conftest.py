from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.db import Base, get_async_session
from app.crud.user import user_crud
from app.main import app
from app.models.user import User
from app.schemas.status_enum import UserRole
from app.schemas.user import UserCreate

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    # echo=True,
)

TestingSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

        async with TestingSessionLocal() as session:
            yield session

            await session.rollback()


@pytest.fixture(scope="function")
async def client(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:

    app.dependency_overrides[get_async_session] = lambda: db_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def user(
    db_session: AsyncSession, role: UserRole = UserRole.USER
) -> User:
    user_data = UserCreate(
        name="Test User", phone="+71234567890", password="test_password"
    )
    user = await user_crud.create_user(user_data, db_session)

    if role != UserRole.USER:
        user.role = role
        await db_session.commit()

    return user
