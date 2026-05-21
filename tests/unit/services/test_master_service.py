from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


class TestCheckUniqueness:
    async def test_raises_409_on_duplicate(self, mock_session):
        from app.services.master_service import master_service_manager

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()
        mock_session.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc:
            await master_service_manager._check_uniqueness(
                mock_session,
                service_id=1,
                master_id=1,
            )

        assert exc.value.status_code == 409

    async def test_passes_when_unique(self, mock_session):
        from app.services.master_service import master_service_manager

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        await master_service_manager._check_uniqueness(
            mock_session,
            service_id=1,
            master_id=1,
        )


class TestCreateMasterService:
    async def test_creates_service_for_master(self, mock_session, master_user):
        from app.services.master_service import master_service_manager

        mock_master = MagicMock()
        mock_master.id = 1
        created = MagicMock()

        request = MagicMock()
        request.service_id = 1

        with (
            patch.object(
                master_service_manager.master_manager,
                'get_master_by_user_id',
                new=AsyncMock(return_value=mock_master),
            ),
            patch.object(
                master_service_manager,
                'validate_create_common',
                new=AsyncMock(),
            ),
            patch.object(
                master_service_manager,
                'create',
                new=AsyncMock(return_value=created),
            ),
        ):
            result = await master_service_manager.create_master_service(
                mock_session,
                request,
                master_user,
            )

        assert result is created


class TestCreateMasterServiceAdmin:
    async def test_creates_service_for_master_admin(self, mock_session):
        from app.services.master_service import master_service_manager

        request = MagicMock()
        request.model_dump.return_value = {
            'service_id': 1,
            'price': 1000,
            'description': 'test',
            'duration': 3600,
        }
        created = MagicMock()

        with (
            patch.object(
                master_service_manager,
                'validate_create_common',
                new=AsyncMock(),
            ),
            patch.object(
                master_service_manager,
                'create',
                new=AsyncMock(return_value=created),
            ),
        ):
            result = await master_service_manager.create_master_service_admin(
                mock_session,
                request,
                master_id=1,
            )

        assert result is created


class TestUpdateMasterService:
    async def test_owner_can_update(self, mock_session, master_user):
        from app.services.master_service import master_service_manager

        mock_master = MagicMock()
        mock_master.id = 1
        mock_service = MagicMock()
        mock_service.master_id = 1
        updated = MagicMock()

        with (
            patch.object(
                master_service_manager.master_manager,
                'get_master_by_user_id',
                new=AsyncMock(return_value=mock_master),
            ),
            patch.object(
                master_service_manager,
                'get_object_or_404',
                new=AsyncMock(return_value=mock_service),
            ),
            patch.object(
                master_service_manager,
                'update',
                new=AsyncMock(return_value=updated),
            ),
        ):
            result = await master_service_manager.update_master_service(
                mock_session,
                master_service_id=1,
                request=MagicMock(),
                user=master_user,
            )

        assert result is updated

    async def test_other_master_raises_403(self, mock_session, master_user):
        from app.services.master_service import master_service_manager

        mock_master = MagicMock()
        mock_master.id = 1
        mock_service = MagicMock()
        mock_service.master_id = 999

        with (
            patch.object(
                master_service_manager.master_manager,
                'get_master_by_user_id',
                new=AsyncMock(return_value=mock_master),
            ),
            patch.object(
                master_service_manager,
                'get_object_or_404',
                new=AsyncMock(return_value=mock_service),
            ),
        ):
            with pytest.raises(HTTPException) as exc:
                await master_service_manager.update_master_service(
                    mock_session,
                    master_service_id=1,
                    request=MagicMock(),
                    user=master_user,
                )

        assert exc.value.status_code == 403

    async def test_admin_can_update_any_service(
        self, mock_session, admin_user,
    ):
        from app.services.master_service import master_service_manager

        mock_master = MagicMock()
        mock_master.id = 1
        mock_service = MagicMock()
        mock_service.master_id = 999
        updated = MagicMock()

        with (
            patch.object(
                master_service_manager.master_manager,
                'get_master',
                new=AsyncMock(return_value=mock_master),
            ),
            patch.object(
                master_service_manager,
                'get_object_or_404',
                new=AsyncMock(return_value=mock_service),
            ),
            patch.object(
                master_service_manager,
                'update',
                new=AsyncMock(return_value=updated),
            ),
        ):
            result = await master_service_manager.update_master_service(
                mock_session,
                master_service_id=1,
                request=MagicMock(),
                user=admin_user,
                master_id=1,
            )

        assert result is updated


class TestGetMasterService:
    async def test_returns_service_when_found(self, mock_session):
        from app.services.master_service import master_service_manager

        mock_master = MagicMock()
        mock_service = MagicMock()

        with (
            patch.object(
                master_service_manager.master_manager,
                'get_object_or_404',
                new=AsyncMock(return_value=mock_master),
            ),
            patch.object(
                master_service_manager.crud,
                'get_master_service',
                new=AsyncMock(return_value=mock_service),
            ),
        ):
            result = await master_service_manager.get_master_service(
                mock_session,
                master_id=1,
                service_id=1,
            )

        assert result is mock_service

    async def test_raises_404_when_not_found(self, mock_session):
        from app.services.master_service import master_service_manager

        mock_master = MagicMock()

        with (
            patch.object(
                master_service_manager.master_manager,
                'get_object_or_404',
                new=AsyncMock(return_value=mock_master),
            ),
            patch.object(
                master_service_manager.crud,
                'get_master_service',
                new=AsyncMock(return_value=None),
            ),
        ):
            with pytest.raises(HTTPException) as exc:
                await master_service_manager.get_master_service(
                    mock_session,
                    master_id=1,
                    service_id=1,
                )

        assert exc.value.status_code == 404


class TestGetMyService:
    async def test_returns_service_when_found(self, mock_session, master_user):
        from app.services.master_service import master_service_manager

        mock_master = MagicMock()
        mock_master.id = 1
        mock_service = MagicMock()

        with (
            patch.object(
                master_service_manager.master_manager,
                'get_master_by_user_id',
                new=AsyncMock(return_value=mock_master),
            ),
            patch.object(
                master_service_manager.crud,
                'get_master_service',
                new=AsyncMock(return_value=mock_service),
            ),
        ):
            result = await master_service_manager.get_my_service(
                mock_session,
                master_user,
                service_id=1,
            )

        assert result is mock_service

    async def test_raises_404_when_not_found(self, mock_session, master_user):
        from app.services.master_service import master_service_manager

        mock_master = MagicMock()
        mock_master.id = 1

        with (
            patch.object(
                master_service_manager.master_manager,
                'get_master_by_user_id',
                new=AsyncMock(return_value=mock_master),
            ),
            patch.object(
                master_service_manager.crud,
                'get_master_service',
                new=AsyncMock(return_value=None),
            ),
        ):
            with pytest.raises(HTTPException) as exc:
                await master_service_manager.get_my_service(
                    mock_session,
                    master_user,
                    service_id=1,
                )

        assert exc.value.status_code == 404
