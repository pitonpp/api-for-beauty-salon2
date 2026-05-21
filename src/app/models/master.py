from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, CommonBaseMixin

if TYPE_CHECKING:
    from app.models.master_service import MasterService


class Master(CommonBaseMixin, Base):
    """Модель мастера с информацией об опыте и биографии."""

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id"),
        nullable=False,
    )
    bio: Mapped[str] = mapped_column(
        Text,
        nullable=True,
    )
    experience: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    master_services: Mapped[list["MasterService"]] = relationship(
        "MasterService",
        back_populates="master",
        cascade="all, delete-orphan",
    )
