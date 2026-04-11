from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.db import Base, CommonBaseMixin
from src.app.schemas.status_enum import AppointmentStatus


class Appointment(CommonBaseMixin, Base):
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=False
    )
    service_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("service.id"), nullable=False
    )
    appointment_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED.value
    )

    user: Mapped["User"] = relationship("User", back_populates="appointments")
    service: Mapped["Service"] = relationship(
        "Service", back_populates="appointments"
    )
