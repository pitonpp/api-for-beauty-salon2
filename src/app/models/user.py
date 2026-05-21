from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, CommonBaseMixin
from app.schemas.status_enum import UserRole

if TYPE_CHECKING:
    from app.models.appointment import Appointment


class User(CommonBaseMixin, Base):
    """Модель пользователя (клиент, мастер, администратор)."""

    phone: Mapped[str] = mapped_column(
        String(12),
        unique=True,
        nullable=False,
        comment='Номер телефона пользователя в формате +7XXXXXXXXXX',
    )
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        comment='Уникальное имя пользователя (логин)',
    )
    email: Mapped[str] = mapped_column(
        String(200),
        unique=True,
        nullable=False,
        index=True,
    )
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment='Имя пользователя',
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
        comment='Фамилия пользователя',
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        default=UserRole.USER.value,
        nullable=False,
        comment='Роль пользователя',
    )
    password: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment='Хэшированный пароль',
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment='Активен ли пользователь',
    )

    appointments: Mapped['Appointment'] = relationship(
        'Appointment',
        back_populates='user',
    )

    @property
    def is_admin(self) -> bool:
        """Проверяет, является ли пользователь администратором."""
        return self.role == UserRole.ADMIN
