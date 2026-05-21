from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.schemas.appointment import (
    AppointmentAdminCreate,
    AppointmentCreate,
    AppointmentUpdate,
)
from app.schemas.status_enum import AppointmentStatus
from app.services.appointment import appointment_service
from tests.integration.factories import make_master_service, make_user

FUTURE = datetime.now(timezone.utc) + timedelta(days=14)


@pytest.fixture(autouse=True)
def _mock_celery():
    with patch(
        'app.services.appointment.send_appointment_notification.delay',
    ) as mock:
        yield mock


@pytest.mark.integration
class TestAppointmentIntegration:
    async def test_create_and_get_appointment(self, session):
        user = await make_user(
            session,
            username='appoint_user',
            email='appoint@test.com',
            phone='+79234567890',
        )
        ms = await make_master_service(session)

        request = AppointmentCreate(appointment_time=FUTURE)
        appointment = await appointment_service.create_appointment(
            request=request,
            session=session,
            user=user,
            master_service_id=ms.id,
        )

        assert appointment.id is not None
        assert appointment.status.name == 'SCHEDULED'

        fetched = await appointment_service.get_user_appointment(
            session,
            user,
            appointment.id,
        )
        assert fetched.id == appointment.id

    async def test_cancel_appointment(self, session):
        user = await make_user(
            session,
            username='cancel_user',
            email='cancel@test.com',
            phone='+79234567891',
        )
        ms = await make_master_service(session)

        request = AppointmentCreate(appointment_time=FUTURE)
        appointment = await appointment_service.create_appointment(
            request=request,
            session=session,
            user=user,
            master_service_id=ms.id,
        )

        cancel_request = AppointmentUpdate(status=AppointmentStatus.CANCELED)
        cancelled = await appointment_service.update_appointment(
            request=cancel_request,
            session=session,
            appointment_id=appointment.id,
            user=user,
        )

        assert cancelled.status == AppointmentStatus.CANCELED

    async def test_admin_creates_appointment(self, session):
        user = await make_user(
            session,
            username='admin_create_user',
            email='admin_create@test.com',
            phone='+79234567892',
        )
        ms = await make_master_service(session)

        request = AppointmentAdminCreate(
            appointment_time=FUTURE,
            master_service_id=ms.id,
            user_id=user.id,
        )
        appointment = await appointment_service.admin_create_appointment(
            request=request,
            session=session,
        )

        assert appointment.id is not None
