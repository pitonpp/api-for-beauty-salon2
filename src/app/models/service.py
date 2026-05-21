from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, CommonBaseMixin

if TYPE_CHECKING:
    from app.models.master_service import MasterService


class Service(CommonBaseMixin, Base):
    """Модель услуги салона (например, стрижка, маникюр)."""

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        comment='Название услуги',
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment='Активна ли услуга',
    )

    master_services: Mapped[list['MasterService']] = relationship(
        'MasterService',
        back_populates='service',
    )
