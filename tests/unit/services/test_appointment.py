from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

FUTURE = datetime(2027, 6, 1, tzinfo=timezone.utc)


class TestCheckPermissions:
    """AppointmentService._check_permissions — чистая логика без моков."""

    def test_admin_can_access_any_appointment(
        self, appointment_service_, admin_user,
    ):
        service = appointment_service_
        appointment = MagicMock()
        appointment.client_id = 999

        service._check_permissions(admin_user, appointment)

    def test_owner_can_access_own_appointment(
        self, appointment_service_, regular_user,
    ):
        service = appointment_service_
        appointment = MagicMock()
        appointment.client_id = regular_user.id

        service._check_permissions(regular_user, appointment)

    def test_other_user_raises_403(self, appointment_service_, regular_user):
        service = appointment_service_
        appointment = MagicMock()
        appointment.client_id = 999

        with pytest.raises(HTTPException) as exc:
            service._check_permissions(regular_user, appointment)

        assert exc.value.status_code == 403

    def test_none_user_raises_attribute_error(self, appointment_service_):
        service = appointment_service_
        appointment = MagicMock()
        appointment.client_id = 1

        with pytest.raises(AttributeError):
            service._check_permissions(None, appointment)

    def test_none_appointment_raises_attribute_error(
        self,
        appointment_service_,
        regular_user,
    ):
        service = appointment_service_

        with pytest.raises(AttributeError):
            service._check_permissions(regular_user, None)

    def test_master_role_obeys_same_rule(
        self, appointment_service_, master_user,
    ):
        service = appointment_service_

        own = MagicMock()
        own.client_id = master_user.id
        service._check_permissions(master_user, own)

        others = MagicMock()
        others.client_id = 999
        with pytest.raises(HTTPException) as exc:
            service._check_permissions(master_user, others)

        assert exc.value.status_code == 403


class TestCheckTimeAvailable:
    """AppointmentService.check_time_available — БД-мок, но проверяем
    бизнес-логику: past check, overlap, boundary, zero duration.
    """

    async def test_past_time_raises_400(
        self, appointment_service_, mock_session,
    ):
        service = appointment_service_

        with pytest.raises(HTTPException) as exc:
            await service.check_time_available(
                appointment_time=datetime(2020, 1, 1, tzinfo=timezone.utc),
                session=mock_session,
                duration=timedelta(hours=1),
            )

        assert exc.value.status_code == 400

    async def test_same_day_passes_past_check(
        self, appointment_service_, mock_session,
    ):
        """Граница: appointment_time.date() == now не должно кидать 400."""
        service = appointment_service_
        today = datetime.now(timezone.utc) + timedelta(hours=1)

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute.return_value = mock_result

        await service.check_time_available(
            appointment_time=today,
            session=mock_session,
            duration=timedelta(hours=1),
        )

    async def test_overlap_raises_409(
        self, appointment_service_, mock_session,
    ):
        service = appointment_service_
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = MagicMock()
        mock_session.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc:
            await service.check_time_available(
                appointment_time=FUTURE,
                session=mock_session,
                duration=timedelta(hours=1),
            )

        assert exc.value.status_code == 409

    async def test_adjacent_times_are_ok(
        self, appointment_service_, mock_session,
    ):
        """[10:00, 11:00) и [11:00, 12:00) — не пересечение."""
        service = appointment_service_
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute.return_value = mock_result

        await service.check_time_available(
            appointment_time=FUTURE + timedelta(hours=1),
            session=mock_session,
            duration=timedelta(hours=1),
        )

    async def test_exclude_id_ignores_conflict(
        self, appointment_service_, mock_session,
    ):
        service = appointment_service_
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute.return_value = mock_result

        await service.check_time_available(
            appointment_time=FUTURE,
            session=mock_session,
            duration=timedelta(hours=1),
            exclude_id=999,
        )

    async def test_non_scheduled_overlap_is_ok(
        self,
        appointment_service_,
        mock_session,
    ):
        """Пересечение с отменённой/выполненной — не 409."""
        service = appointment_service_
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute.return_value = mock_result

        await service.check_time_available(
            appointment_time=FUTURE,
            session=mock_session,
            duration=timedelta(hours=1),
        )

    async def test_zero_duration_does_not_crash(
        self,
        appointment_service_,
        mock_session,
    ):
        service = appointment_service_
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute.return_value = mock_result

        await service.check_time_available(
            appointment_time=FUTURE,
            session=mock_session,
            duration=timedelta(seconds=0),
        )


class TestUpdateAppointment:
    """AppointmentService.update_appointment — ветвление по времени."""

    async def test_skips_time_check_when_no_time_provided(
        self,
        appointment_service_,
        mock_session,
        regular_user,
    ):
        service = appointment_service_
        request = MagicMock()
        request.appointment_time = None

        mock_appointment = MagicMock()
        mock_appointment.client_id = regular_user.id

        mock_check_time = AsyncMock()

        with (
            patch.object(
                service,
                'get_object_or_404',
                AsyncMock(return_value=mock_appointment),
            ),
            patch.object(service, 'check_time_available', mock_check_time),
            patch.object(service.crud, 'update', AsyncMock()),
        ):
            await service.update_appointment(
                request=request,
                session=mock_session,
                appointment_id=1,
                user=regular_user,
            )

        mock_check_time.assert_not_called()

    async def test_checks_time_when_time_provided(
        self,
        appointment_service_,
        mock_session,
        regular_user,
    ):
        service = appointment_service_
        request = MagicMock()
        request.appointment_time = FUTURE

        master_service = MagicMock()
        master_service.duration = timedelta(hours=1)

        mock_appointment = MagicMock()
        mock_appointment.client_id = regular_user.id
        mock_appointment.master_service_id = 1

        mock_check_time = AsyncMock()

        with (
            patch.object(
                service,
                'get_object_or_404',
                AsyncMock(return_value=mock_appointment),
            ),
            patch.object(
                service.master_service_manager,
                'get_object_or_404',
                AsyncMock(return_value=master_service),
            ),
            patch.object(service, 'check_time_available', mock_check_time),
            patch.object(service.crud, 'update', AsyncMock()),
        ):
            await service.update_appointment(
                request=request,
                session=mock_session,
                appointment_id=1,
                user=regular_user,
            )

        mock_check_time.assert_called_once_with(
            FUTURE,
            mock_session,
            master_service.duration,
        )

    async def test_raises_403_for_others(
        self,
        appointment_service_,
        mock_session,
        regular_user,
    ):
        service = appointment_service_
        mock_appointment = MagicMock()
        mock_appointment.client_id = 999

        with patch.object(
            service,
            'get_object_or_404',
            AsyncMock(return_value=mock_appointment),
        ):
            with pytest.raises(HTTPException) as exc:
                await service.update_appointment(
                    request=MagicMock(),
                    session=mock_session,
                    appointment_id=1,
                    user=regular_user,
                )

            assert exc.value.status_code == 403


class TestAdminCreateAppointment:
    async def test_creates_via_create_appointment(
        self, appointment_service_, mock_session,
    ):
        service = appointment_service_
        request = MagicMock()
        request.model_dump.return_value = {
            'appointment_time': FUTURE,
            'master_service_id': 1,
            'user_id': 1,
        }

        mock_appointment = MagicMock()
        mock_appointment.id = 1

        with (
            patch.object(
                service,
                '_validate_and_get_service_and_master',
                new=AsyncMock(),
            ),
            patch.object(
                service.crud,
                'create',
                new=AsyncMock(return_value=mock_appointment),
            ),
            patch(
                'app.services.appointment.send_appointment_notification.delay',
            ),
        ):
            result = await service.admin_create_appointment(
                request=request, session=mock_session,
            )
            assert result is mock_appointment


class TestAdminUpdateAppointment:
    async def test_updates_time_and_master_service(
        self, appointment_service_, mock_session,
    ):
        service = appointment_service_
        request = MagicMock()
        request.appointment_time = FUTURE
        request.master_service_id = 2

        mock_appointment = MagicMock()
        mock_appointment.master_service_id = 1
        mock_appointment.appointment_time = FUTURE + timedelta(days=1)

        new_master_service = MagicMock()
        new_master_service.duration = timedelta(hours=2)

        with (
            patch.object(
                service,
                'get_object_or_404',
                new=AsyncMock(return_value=mock_appointment),
            ),
            patch.object(
                service.master_service_manager,
                'get_object_or_404',
                new=AsyncMock(return_value=new_master_service),
            ),
            patch.object(service, 'check_time_available') as mock_check_time,
            patch.object(
                service.crud,
                'update',
                new=AsyncMock(return_value=mock_appointment),
            ),
        ):
            result = await service.admin_update_appointment(
                request=request,
                session=mock_session,
                appointment_id=1,
            )
            assert result is mock_appointment
            mock_check_time.assert_called_once()

    async def test_skips_time_check_when_no_changes(
        self, appointment_service_, mock_session,
    ):
        service = appointment_service_
        request = MagicMock()
        request.appointment_time = None
        request.master_service_id = None

        mock_appointment = MagicMock()
        mock_appointment.master_service_id = 1
        mock_appointment.appointment_time = FUTURE

        with (
            patch.object(
                service,
                'get_object_or_404',
                new=AsyncMock(return_value=mock_appointment),
            ),
            patch.object(service, 'check_time_available') as mock_check,
            patch.object(service.crud, 'update', new=AsyncMock()),
        ):
            await service.admin_update_appointment(
                request=request,
                session=mock_session,
                appointment_id=1,
            )

        mock_check.assert_not_called()


class TestMasterUpdateAppointment:
    async def test_updates_status(self, appointment_service_, mock_session):
        service = appointment_service_
        request = MagicMock()

        mock_appointment = MagicMock()

        with (
            patch.object(
                service,
                'get_object_or_404',
                new=AsyncMock(return_value=mock_appointment),
            ),
            patch.object(
                service.crud,
                'update',
                new=AsyncMock(return_value=mock_appointment),
            ),
        ):
            result = await service.master_update_appointment(
                request=request,
                session=mock_session,
                appointment_id=1,
            )

        assert result is mock_appointment


class TestValidateAndGetServiceAndMaster:
    async def test_returns_master_service(
        self, appointment_service_, mock_session,
    ):
        service = appointment_service_
        mock_master_service = MagicMock()
        mock_master_service.duration = timedelta(hours=1)

        with (
            patch.object(
                service.master_service_manager,
                'get_object_or_404',
                new=AsyncMock(return_value=mock_master_service),
            ),
            patch.object(service, 'check_time_available', new=AsyncMock()),
        ):
            result = await service._validate_and_get_service_and_master(
                appointment_time=FUTURE,
                session=mock_session,
                master_service_id=1,
            )

        assert result is mock_master_service
