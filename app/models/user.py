from datetime import datetime

from sqlalchemy import String, DateTime, func, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, CommonBaseMixin
from app.schemas.status_enum import UserRole


class User(CommonBaseMixin, Base):
    phone: Mapped[str] = mapped_column(
        String(12), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.CLIENT.value, nullable=False
    )
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    appointments: Mapped["Appointment"] = relationship(
        "Appointment", back_populates="user"
    )
