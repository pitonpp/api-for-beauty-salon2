from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    Interval,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, CommonBaseMixin


class MasterService(CommonBaseMixin, Base):
    """Связь мастера и услуги: цена, описание, длительность."""

    master_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('master.id'),
        nullable=False,
        comment='ID мастера',
    )
    service_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('service.id'),
        nullable=False,
        comment='ID услуги',
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(precision=8, scale=2),
        nullable=False,
        comment='Стоимость услуги',
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='Описание услуги',
    )
    duration: Mapped[timedelta] = mapped_column(
        Interval,
        nullable=False,
        comment='Длительность услуги',
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment='Активна ли услуга',
    )

    master: Mapped['Master'] = relationship(
        'Master',
        back_populates='master_services',
    )
    service: Mapped['Service'] = relationship(
        'Service',
        back_populates='master_services',
    )
    appointments: Mapped[list['Appointment']] = relationship(
        'Appointment',
        back_populates='master_service',
    )

    __table_args__ = (
        UniqueConstraint(
            'service_id',
            'master_id',
            name='uq_service_master',
        ),
    )

    @property
    def service_name(self) -> str:
        """Возвращает название услуги."""
        return self.service.name


if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.master import Master
    from app.models.service import Service
