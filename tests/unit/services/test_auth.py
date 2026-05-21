from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request

from app.schemas.status_enum import UserRole


class TestRoleCheck:
    """AuthService.role_check — логика проверки ролей."""

    async def test_allowed_role_passes(self, auth_service_, mock_session):
        auth_service = auth_service_
        checker = auth_service.role_check(UserRole.USER, UserRole.ADMIN)

        mock_user = MagicMock()
        mock_user.role = UserRole.ADMIN

        with (
            patch.object(
                auth_service,
                'get_token_from_request',
                return_value='tok',
            ),
            patch.object(
                auth_service,
                'get_current_user',
                new=AsyncMock(return_value=mock_user),
            ),
        ):
            result = await checker(session=mock_session, request=MagicMock())

        assert result is mock_user

    async def test_wrong_role_raises_403(self, auth_service_, mock_session):
        auth_service = auth_service_
        checker = auth_service.role_check(UserRole.ADMIN)

        mock_user = MagicMock()
        mock_user.role = UserRole.USER

        with (
            patch.object(
                auth_service,
                'get_token_from_request',
                return_value='tok',
            ),
            patch.object(
                auth_service,
                'get_current_user',
                new=AsyncMock(return_value=mock_user),
            ),
        ):
            with pytest.raises(HTTPException) as exc:
                await checker(session=mock_session, request=MagicMock())

        assert exc.value.status_code == 403

    async def test_empty_allowed_roles_denies_all(
        self,
        auth_service_,
        mock_session,
    ):
        auth_service = auth_service_
        checker = auth_service.role_check()

        mock_user = MagicMock()
        mock_user.role = UserRole.ADMIN

        with (
            patch.object(
                auth_service,
                'get_token_from_request',
                return_value='tok',
            ),
            patch.object(
                auth_service,
                'get_current_user',
                new=AsyncMock(return_value=mock_user),
            ),
        ):
            with pytest.raises(HTTPException) as exc:
                await checker(session=mock_session, request=MagicMock())

        assert exc.value.status_code == 403

    async def test_allow_users_includes_master(
        self,
        auth_service_,
        mock_session,
    ):
        auth_service = auth_service_
        checker = auth_service.allow_users()

        for role in (UserRole.USER, UserRole.ADMIN, UserRole.MASTER):
            mock_user = MagicMock()
            mock_user.role = role
            with (
                patch.object(
                    auth_service,
                    'get_token_from_request',
                    return_value='tok',
                ),
                patch.object(
                    auth_service,
                    'get_current_user',
                    new=AsyncMock(return_value=mock_user),
                ),
            ):
                result = await checker(
                    session=mock_session,
                    request=MagicMock(),
                )
                assert result.role == role


class TestGetTokenFromRequest:
    """AuthService.get_token_from_request — парсинг заголовков."""

    def test_bearer_token_returns_token(self, auth_service_):
        auth_service = auth_service_
        request = MagicMock(spec=Request)
        request.headers.get.return_value = 'Bearer mysecrettoken'

        result = auth_service.get_token_from_request(request)

        assert result == 'mysecrettoken'

    def test_no_auth_header_falls_to_cookie(self, auth_service_):
        auth_service = auth_service_
        request = MagicMock(spec=Request)
        request.headers.get.return_value = None

        with patch.object(
            auth_service,
            '_get_token_from_cookie',
            return_value='cookie_token',
        ) as mock_cookie:
            result = auth_service.get_token_from_request(request)

            assert result == 'cookie_token'
            mock_cookie.assert_called_once_with(request, True)

    def test_non_bearer_auth_falls_to_cookie(self, auth_service_):
        auth_service = auth_service_
        request = MagicMock(spec=Request)
        request.headers.get.return_value = 'Basic dXNlcjpwYXNz'

        with patch.object(
            auth_service,
            '_get_token_from_cookie',
            return_value='cookie_token',
        ):
            result = auth_service.get_token_from_request(request)

        assert result == 'cookie_token'

    def test_bearer_with_empty_token(self, auth_service_):
        auth_service = auth_service_
        request = MagicMock(spec=Request)
        request.headers.get.return_value = 'Bearer '

        result = auth_service.get_token_from_request(request)

        assert result == ''

    def test_cookie_raises_when_no_token(self, auth_service_):
        auth_service = auth_service_
        request = MagicMock(spec=Request)
        request.headers.get.return_value = None

        with patch.object(
            auth_service,
            '_get_token_from_cookie',
            side_effect=HTTPException(status_code=401),
        ):
            with pytest.raises(HTTPException) as exc:
                auth_service.get_token_from_request(request)

        assert exc.value.status_code == 401


class TestLogin:
    """AuthService.login — логика ветвления с моком verify_password."""

    async def test_user_not_found_skips_password_check(
        self,
        auth_service_,
        mock_session,
    ):
        """Short-circuit OR: если user None, verify_password НЕ вызывается."""
        auth_service = auth_service_

        with (
            patch.object(
                auth_service,
                'get_by_username',
                new=AsyncMock(return_value=None),
            ),
            patch('app.services.auth.verify_password') as mock_verify,
        ):
            with pytest.raises(HTTPException) as exc:
                await auth_service.login(
                    mock_session,
                    'nobody',
                    'anypass',
                    MagicMock(),
                )

        assert exc.value.status_code == 401
        mock_verify.assert_not_called()

    async def test_delete_user_password_raises_attribute_error(
        self,
        auth_service_,
        mock_session,
    ):
        """Если у user нет password — AttributeError (должен упасть 500)."""
        auth_service = auth_service_
        user_no_pass = MagicMock(spec=[])
        del user_no_pass.password

        with (
            patch.object(
                auth_service,
                'get_by_username',
                new=AsyncMock(return_value=user_no_pass),
            ),
            patch('app.services.auth.verify_password', return_value=False),
        ):
            with pytest.raises(AttributeError):
                await auth_service.login(
                    mock_session,
                    'hacker',
                    'anypass',
                    MagicMock(),
                )

    async def test_inactive_user_raises_403_before_token_creation(
        self,
        auth_service_,
        mock_session,
    ):
        """Проверка: блокировка проверяется ДО создания токенов."""
        auth_service = auth_service_
        mock_user = MagicMock()
        mock_user.is_active = False
        mock_user.password = 'hash'

        mock_create_tokens = AsyncMock()

        with (
            patch.object(
                auth_service,
                'get_by_username',
                new=AsyncMock(return_value=mock_user),
            ),
            patch('app.services.auth.verify_password', return_value=True),
            patch.object(
                auth_service.token_service,
                'create_tokens',
                mock_create_tokens,
            ),
        ):
            with pytest.raises(HTTPException) as exc:
                await auth_service.login(
                    mock_session,
                    'blocked',
                    'pass',
                    MagicMock(),
                )

            assert exc.value.status_code == 403
            mock_create_tokens.assert_not_called()
