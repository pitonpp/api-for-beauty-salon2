from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.schemas.user import UserCreate, UserUpdate, UserUpdateAdmin


class TestValidateAdminSelfUpdate:
    """UserService.validate_admin_self_update — чистая логика без моков."""

    def test_self_deactivate_raises_403(self, user_service_, admin_user):
        service = user_service_
        request = UserUpdateAdmin(is_active=False)

        with pytest.raises(HTTPException) as exc:
            service.validate_admin_self_update(admin_user, admin_user, request)

        assert exc.value.status_code == 403

    def test_self_update_with_active_true_is_ok(self, user_service_, admin_user):
        service = user_service_
        request = UserUpdateAdmin(is_active=True)

        service.validate_admin_self_update(admin_user, admin_user, request)

    def test_self_update_with_is_active_none_is_ok(self, user_service_, admin_user):
        service = user_service_
        request = UserUpdateAdmin(is_active=None)

        service.validate_admin_self_update(admin_user, admin_user, request)

    def test_deactivate_other_user_is_ok(self, user_service_, admin_user):
        service = user_service_
        other = MagicMock()
        other.id = 999
        request = UserUpdateAdmin(is_active=False)

        service.validate_admin_self_update(other, admin_user, request)

    def test_none_current_user_raises_attribute_error(
        self, user_service_, admin_user,
    ):
        service = user_service_
        request = UserUpdateAdmin(is_active=False)

        with pytest.raises(AttributeError):
            service.validate_admin_self_update(admin_user, None, request)


class TestAddPasswordHash:
    """UserService._add_password_hash — чистая логика хеширования."""

    def test_adds_hash_when_password_present(self, user_service_):
        service = user_service_
        data = {"password": "Str0ng!Pass", "username": "test"}

        with patch("app.services.user.hash_password", return_value="hashed"):
            result = service._add_password_hash(data)

        assert result["password"] == "hashed"
        assert result["username"] == "test"

    def test_returns_new_dict_not_mutating_original(self, user_service_):
        service = user_service_
        data = {"password": "Str0ng!Pass"}

        with patch("app.services.user.hash_password", return_value="hashed"):
            result = service._add_password_hash(data)

        assert result is not data
        assert data["password"] == "Str0ng!Pass"

    def test_password_none_returns_same_dict(self, user_service_):
        service = user_service_
        data = {"password": None, "username": "test"}

        result = service._add_password_hash(data)

        assert result is data
        assert "password" in result

    def test_no_password_key_returns_same_dict(self, user_service_):
        service = user_service_
        data = {"username": "test"}

        result = service._add_password_hash(data)

        assert result is data

    def test_empty_dict_returns_same_dict(self, user_service_):
        service = user_service_
        data = {}

        result = service._add_password_hash(data)

        assert result is data


class TestUpdateUser:
    """UserService.update_user — проверка ветвления между UserUpdate и UserUpdateAdmin."""

    async def test_user_update_does_not_call_admin_validation(
        self, user_service_, session, admin_user,
    ):
        """UserUpdate (не UserUpdateAdmin) — validate_admin_self_update не вызывается."""
        service = user_service_
        request = UserUpdate(first_name="Новое")

        with (
            patch.object(
                service, "get_object_or_404",
                AsyncMock(return_value=admin_user),
            ),
            patch.object(service, "validate_admin_self_update") as mock_validate,
            patch.object(
                service.crud, "update",
                AsyncMock(return_value=admin_user),
            ),
        ):
            await service.update_user(
                user_id=admin_user.id,
                session=session,
                request=request,
                current_user=admin_user,
            )

        mock_validate.assert_not_called()

    async def test_admin_update_calls_admin_validation(
        self, user_service_, session, admin_user,
    ):
        """UserUpdateAdmin — validate_admin_self_update вызывается."""
        service = user_service_
        request = UserUpdateAdmin(is_active=True)
        other_user = MagicMock()
        other_user.id = 999

        with (
            patch.object(
                service, "get_object_or_404",
                AsyncMock(return_value=other_user),
            ),
            patch.object(service, "validate_admin_self_update") as mock_validate,
            patch.object(service.crud, "update", AsyncMock()),
        ):
            await service.update_user(
                user_id=999, session=session,
                request=request, current_user=admin_user,
            )

        mock_validate.assert_called_once_with(other_user, admin_user, request)
