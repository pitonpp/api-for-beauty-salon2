import pytest
from sqlalchemy.exc import IntegrityError

from app.crud.user import user_crud
from app.schemas.status_enum import UserRole


class TestCRUDUser:
    async def test_create_user(self, session):
        data = {
            "phone": "+79234567890",
            "username": "ivanov",
            "email": "ivanov@test.com",
            "first_name": "Иван",
            "last_name": "Иванов",
            "role": UserRole.USER,
            "password": "hashed_secret",
            "is_active": True,
        }

        user = await user_crud.create(data, session)

        assert user.id is not None
        assert user.username == "ivanov"
        assert user.email == "ivanov@test.com"
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.password == "hashed_secret"
        assert user.created_at is not None

    async def test_get_user_by_id(self, session):
        data = {
            "phone": "+79234567891",
            "username": "petrov",
            "email": "petrov@test.com",
            "first_name": "Петр",
            "password": "hash",
            "role": UserRole.USER,
        }
        created = await user_crud.create(data, session)
        session_id = created.id

        fetched = await user_crud.get(session_id, session)

        assert fetched is not None
        assert fetched.id == session_id
        assert fetched.username == "petrov"

    async def test_get_user_by_username(self, session):
        data = {
            "phone": "+79234567892",
            "username": "sidorov",
            "email": "sidorov@test.com",
            "first_name": "Сидр",
            "password": "hash",
            "role": UserRole.USER,
        }
        await user_crud.create(data, session)

        fetched = await user_crud.get_one_by(session, username="sidorov")

        assert fetched is not None
        assert fetched.username == "sidorov"

    async def test_update_user(self, session):
        data = {
            "phone": "+79234567893",
            "username": "update_me",
            "email": "update@test.com",
            "first_name": "Обнов",
            "password": "old_hash",
            "role": UserRole.USER,
        }
        user = await user_crud.create(data, session)

        updated = await user_crud.update(
            user, {"first_name": "Обновлен", "last_name": "Обновленко"}, session,
        )

        assert updated.first_name == "Обновлен"
        assert updated.last_name == "Обновленко"
        assert updated.username == "update_me"

    async def test_duplicate_username_raises_integrity_error(self, session):
        data = {
            "phone": "+79234567894",
            "username": "unique_user",
            "email": "first@test.com",
            "first_name": "Первый",
            "password": "hash",
            "role": UserRole.USER,
        }
        await user_crud.create(data, session)

        dup = {
            "phone": "+79234567895",
            "username": "unique_user",
            "email": "second@test.com",
            "first_name": "Второй",
            "password": "hash",
            "role": UserRole.USER,
        }
        with pytest.raises(IntegrityError):
            await user_crud.create(dup, session)

    async def test_delete_user(self, session):
        data = {
            "phone": "+79234567896",
            "username": "to_delete",
            "email": "delete@test.com",
            "first_name": "Дел",
            "password": "hash",
            "role": UserRole.USER,
        }
        user = await user_crud.create(data, session)
        user_id = user.id

        deleted = await user_crud.delete(user, session)

        assert deleted.id == user_id
        fetched = await user_crud.get(user_id, session)
        assert fetched is None
