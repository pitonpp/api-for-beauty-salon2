from datetime import timedelta

from sqlalchemy import Interval, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.db import Base, CommonBaseMixin


class Service(CommonBaseMixin, Base):
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    duration: Mapped[timedelta] = mapped_column(Interval, nullable=False)

    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment", back_populates="service"
    )
