from decimal import Decimal
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from app.schemas.status_enum import AppointmentStatus


def make_master_service(**kwargs):
    ms = MagicMock()
    ms.id = kwargs.get("id", 1)
    ms.price = kwargs.get("price", Decimal("1500.00"))
    ms.duration = kwargs.get("duration", timedelta(hours=1))
    ms.service_name = kwargs.get("service_name", "Стрижка")
    return ms


def make_appointment(**kwargs):
    a = MagicMock()
    a.id = kwargs.get("id", 1)
    a.appointment_time = kwargs.get(
        "appointment_time", datetime.now(timezone.utc)
    )
    a.status = kwargs.get("status", AppointmentStatus.SCHEDULED)
    return a
