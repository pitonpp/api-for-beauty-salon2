import pytest
from fastapi import HTTPException

from app.crud.user import user_crud
from app.schemas.user import UserCreate
from app.services.user import user_service


class TestUserService:
    async def test_create_user_persists_and_hashes_password(
        self, session,
    ):
        request = UserCreate(
            phone="+79234567890",
            username="service_user",
            email="service@test.com",
            first_name="Сервис",
            last_name="Тестов",
            password="Str0ng!Pass",
        )

        result = await user_service.create_user(session, request)

        assert result.id is not None
        assert result.username == "service_user"
        assert result.password != "Str0ng!Pass"
        assert result.password.startswith("$2b$")  # bcrypt hash marker

        # verify it's actually in the DB
        from_db = await user_crud.get(result.id, session)
        assert from_db is not None
        assert from_db.username == "service_user"

    async def test_duplicate_username_raises_409(self, session):
        request = UserCreate(
            phone="+79234567891",
            username="conflict_user",
            email="first@test.com",
            first_name="Первый",
            password="Str0ng!Pass",
        )
        await user_service.create_user(session, request)

        duplicate = UserCreate(
            phone="+79234567892",
            username="conflict_user",
            email="second@test.com",
            first_name="Второй",
            password="Str0ng!Pass",
        )

        with pytest.raises(HTTPException) as exc:
            await user_service.create_user(session, duplicate)

        assert exc.value.status_code == 409
