from datetime import timedelta
from decimal import Decimal

from sqlalchemy import Interval, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, CommonBaseMixin


class Service(CommonBaseMixin, Base):
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, comment="Название услуги"
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(precision=6, scale=2), nullable=False, comment="Стоимость услуги"
    )
    duration: Mapped[timedelta] = mapped_column(
        Interval, nullable=False, comment="Длительность услуги"
    )
    description: Mapped[str] = mapped_column(
        Text(500), nullable=False, comment="Описание услуги"
    )

    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment", back_populates="service"
    )
