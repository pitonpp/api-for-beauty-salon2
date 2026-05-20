from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, CommonBaseMixin
from app.models.master import Master
from app.schemas.status_enum import AppointmentStatus


class Appointment(CommonBaseMixin, Base):
    client_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id"),
        nullable=False,
    )
    master_service_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("masterservice.id"),
        nullable=False,
    )
    appointment_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Время записи",
    )
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus),
        default=AppointmentStatus.SCHEDULED.value,
        comment="Статус записи",
    )
    price_at_booking: Mapped[Decimal] = mapped_column(
        Numeric(precision=8, scale=2),
        nullable=False,
        comment="Стоимость услуги",
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="appointments",
    )
    master_service: Mapped["MasterService"] = relationship(
        "MasterService",
        back_populates="appointments",
    )

    @property
    def service_name(self) -> str:
        return self.master_service.service.name

    @property
    def master(self) -> Master:
        return self.master_service.master
