from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.crud.master import master_crud
from app.crud.service import service_crud
from app.crud.master_service import master_service_crud
from app.crud.user import user_crud
from app.schemas.status_enum import UserRole, AppointmentStatus
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentAdminCreate,
)
from app.services.appointment import appointment_service


FUTURE = datetime.now(timezone.utc) + timedelta(days=14)


@pytest.fixture
async def seeded_data(session):
    user = await user_crud.create(
        {
            "phone": "+79234567890",
            "username": "appoint_user",
            "email": "appoint@test.com",
            "first_name": "Тест",
            "password": "hash",
            "role": UserRole.USER,
            "is_active": True,
        },
        session,
    )
    svc = await service_crud.create({"name": "Стрижка"}, session)
    master = await master_crud.create(
        {"user_id": user.id, "bio": "Мастер", "experience": 3},
        session,
    )
    ms = await master_service_crud.create(
        {
            "master_id": master.id,
            "service_id": svc.id,
            "price": 1500.00,
            "description": "Стрижка женская",
            "duration": timedelta(hours=1),
        },
        session,
    )
    return {"user": user, "service": svc, "master": master, "master_service": ms}


@pytest.fixture(autouse=True)
def _mock_celery():
    with patch(
        "app.services.appointment.send_appointment_notification.delay",
    ) as mock:
        yield mock


class TestAppointmentIntegration:
    async def test_create_and_get_appointment(self, session, seeded_data):
        ms = seeded_data["master_service"]
        user = seeded_data["user"]

        request = AppointmentCreate(appointment_time=FUTURE)
        appointment = await appointment_service.create_appointment(
            request=request, session=session, user=user,
            master_service_id=ms.id,
        )

        assert appointment.id is not None
        assert appointment.appointment_time.replace(tzinfo=timezone.utc) == FUTURE
        assert appointment.status.name == "SCHEDULED"

        fetched = await appointment_service.get_user_appointment(
            session, user, appointment.id,
        )
        assert fetched.id == appointment.id

    async def test_cancel_appointment(self, session, seeded_data):
        ms = seeded_data["master_service"]
        user = seeded_data["user"]

        request = AppointmentCreate(appointment_time=FUTURE)
        appointment = await appointment_service.create_appointment(
            request=request, session=session, user=user,
            master_service_id=ms.id,
        )

        cancel_request = AppointmentUpdate(status=AppointmentStatus.CANCELED)
        cancelled = await appointment_service.update_appointment(
            request=cancel_request, session=session,
            appointment_id=appointment.id, user=user,
        )

        assert cancelled.status == AppointmentStatus.CANCELED

    async def test_admin_creates_appointment(self, session, seeded_data):
        ms = seeded_data["master_service"]
        user = seeded_data["user"]

        request = AppointmentAdminCreate(
            appointment_time=FUTURE,
            master_service_id=ms.id,
            user_id=user.id,
        )
        appointment = await appointment_service.admin_create_appointment(
            request=request, session=session,
        )

        assert appointment.id is not None
