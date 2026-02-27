from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
        Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED.value
    )

    client: Mapped["Client"] = relationship(
        "Client", back_populates="appointments"
    )
    service: Mapped["Service"] = relationship(
        "Service", back_populates="appointments"
    )
