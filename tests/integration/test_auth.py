import pytest
from fastapi import HTTPException, Response
from passlib.context import CryptContext

from app.constants import JWT_USER_ID
from app.crud.user import user_crud
from app.schemas.user import Token
from app.services.auth import auth_service
from app.core.jwt_services import token_service

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TestAuthIntegration:
    async def test_login_success(self, session):
        hashed_password = pwd_context.hash("Str0ng!Pass")
        await user_crud.create(
            {
                "phone": "+79234567893",
                "username": "login_user",
                "email": "login@test.com",
                "first_name": "Логин",
                "password": hashed_password,
                "role": "user",
                "is_active": True,
            },
            session,
        )

        response = Response()
        result = await auth_service.login(
            session, "login_user", "Str0ng!Pass", response,
        )

        assert isinstance(result, Token)
        assert result.access_token is not None
        assert result.token_type == "bearer"

    async def test_login_wrong_password_raises_401(self, session):
        hashed_password = pwd_context.hash("Str0ng!Pass")
        await user_crud.create(
            {
                "phone": "+79234567894",
                "username": "wrong_pass_user",
                "email": "wrong@test.com",
                "first_name": "Вронг",
                "password": hashed_password,
                "role": "user",
                "is_active": True,
            },
            session,
        )

        response = Response()
        with pytest.raises(HTTPException) as exc:
            await auth_service.login(
                session, "wrong_pass_user", "WrongPass1", response,
            )

        assert exc.value.status_code == 401

    async def test_login_inactive_user_raises_403(self, session):
        hashed_password = pwd_context.hash("Str0ng!Pass")
        await user_crud.create(
            {
                "phone": "+79234567895",
                "username": "inactive_user",
                "email": "inactive@test.com",
                "first_name": "Инктив",
                "password": hashed_password,
                "role": "user",
                "is_active": False,
            },
            session,
        )

        response = Response()
        with pytest.raises(HTTPException) as exc:
            await auth_service.login(
                session, "inactive_user", "Str0ng!Pass", response,
            )

        assert exc.value.status_code == 403

    async def test_refresh_tokens(self, session):
        from sqlalchemy import select
        from app.models.refresh_token import RefreshToken

        hashed_password = pwd_context.hash("Str0ng!Pass")
        user = await user_crud.create(
            {
                "phone": "+79234567896",
                "username": "refresh_user",
                "email": "refresh@test.com",
                "first_name": "Рефреш",
                "password": hashed_password,
                "role": "user",
                "is_active": True,
            },
            session,
        )

        access_token, refresh_token = await token_service.create_tokens(
            data={JWT_USER_ID: user.id}, session=session,
        )
        assert access_token is not None
        assert refresh_token is not None

        # проверяем что refresh_token есть в БД и не отозван
        token_data = token_service._decode_token(
            refresh_token, token_service.refresh_secret_key,
        )
        token_data = token_service._validate_payload(token_data, "refresh")
        result = await session.execute(
            select(RefreshToken).where(RefreshToken.user_id == user.id),
        )
        db_token = result.scalar_one()
        assert db_token.revoked is False

        # тестируем refresh
        new_access, new_refresh = await token_service.refresh_tokens(
            refresh_token, session,
        )
        assert new_access is not None
        assert new_refresh != refresh_token

        # старый токен должен быть отозван
        await session.refresh(db_token)
        assert db_token.revoked is True

    async def test_logout_revokes_token(self, session):
        from sqlalchemy import select
        from app.models.refresh_token import RefreshToken

        hashed_password = pwd_context.hash("Str0ng!Pass")
        user = await user_crud.create(
            {
                "phone": "+79234567897",
                "username": "logout_user",
                "email": "logout@test.com",
                "first_name": "Логаут",
                "password": hashed_password,
                "role": "user",
                "is_active": True,
            },
            session,
        )

        _, refresh_token = await token_service.create_tokens(
            data={JWT_USER_ID: user.id}, session=session,
        )

        response = Response()
        await auth_service.logout(response, refresh_token, session)

        result = await session.execute(
            select(RefreshToken).where(RefreshToken.user_id == user.id),
        )
        db_token = result.scalar_one()
        assert db_token.revoked is True
