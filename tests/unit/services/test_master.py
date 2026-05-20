from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.schemas.status_enum import UserRole


class TestGetMasterByUserId:
    async def test_returns_master_when_found_and_role_match(
        self, session, master_user,
    ):
        from app.services.master import master_manager

        mock_master = MagicMock()
        mock_master.id = 1

        with patch.object(
            master_manager.crud, "get_one_by", new=AsyncMock(return_value=mock_master),
        ):
            result = await master_manager.get_master_by_user_id(session, master_user)

        assert result is mock_master

    async def test_raises_400_when_master_not_found(self, session, master_user):
        from app.services.master import master_manager

        with patch.object(
            master_manager.crud, "get_one_by", new=AsyncMock(return_value=None),
        ):
            with pytest.raises(HTTPException) as exc:
                await master_manager.get_master_by_user_id(session, master_user)

        assert exc.value.status_code == 400

    async def test_raises_400_when_role_mismatch(self, session, regular_user):
        from app.services.master import master_manager

        mock_master = MagicMock()
        mock_master.id = 1

        with patch.object(
            master_manager.crud, "get_one_by", new=AsyncMock(return_value=mock_master),
        ):
            with pytest.raises(HTTPException) as exc:
                await master_manager.get_master_by_user_id(session, regular_user)

        assert exc.value.status_code == 400


class TestCreateMaster:
    async def test_creates_master_and_changes_role(self, session):
        from app.services.master import master_manager

        request = MagicMock()
        request.user_id = 1

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.role = UserRole.USER

        mock_master = MagicMock()
        mock_master.id = 1

        with (
            patch.object(
                master_manager.user_service, "get_object_or_404",
                new=AsyncMock(return_value=mock_user),
            ),
            patch.object(master_manager, "create", new=AsyncMock(return_value=mock_master)),
        ):
            result = await master_manager.create_master(session, request)

        assert result is mock_master
        assert mock_user.role == UserRole.MASTER


class TestUpdateMaster:
    async def test_updates_master(self, session, master_user):
        from app.services.master import master_manager

        mock_master = MagicMock()
        mock_master.id = 1
        mock_updated = MagicMock()

        with (
            patch.object(
                master_manager, "get_master_by_user_id",
                new=AsyncMock(return_value=mock_master),
            ),
            patch.object(master_manager, "update", new=AsyncMock(return_value=mock_updated)),
        ):
            result = await master_manager.update_master(
                session, master_user, MagicMock(),
            )

        assert result is mock_updated


class TestDowngradeRole:
    async def test_downgrades_master_to_user(self, session):
        from app.services.master import master_manager

        mock_user = MagicMock()
        mock_user.role = UserRole.MASTER

        with patch.object(
            master_manager.user_service, "get_object_or_404",
            new=AsyncMock(return_value=mock_user),
        ):
            result = await master_manager.downgrade_role(session, 1)

        assert result.role == UserRole.USER

    async def test_noop_when_already_user(self, session):
        from app.services.master import master_manager

        mock_user = MagicMock()
        mock_user.role = UserRole.USER

        with patch.object(
            master_manager.user_service, "get_object_or_404",
            new=AsyncMock(return_value=mock_user),
        ):
            result = await master_manager.downgrade_role(session, 1)

        assert result.role == UserRole.USER
