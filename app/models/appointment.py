from datetime import datetime
from typing import List

from sqlalchemy import ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, CommonBaseMixin
from app.schemas.status_enum import AppointmentStatus


class Appointment(CommonBaseMixin, Base):
    client_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("client.id"), nullable=False
    )
    service_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("service.id"), nullable=False
    )
    appointment_time: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[AppointmentStatus] = mapped_column(
        String(50), default=AppointmentStatus.SCHEDULED.value
    )
