from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, CommonBaseMixin


class Service(CommonBaseMixin, Base):
    """Модель услуги салона (например, стрижка, маникюр)."""
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        comment="Название услуги",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Активна ли услуга",
    )

    master_services: Mapped[list["MasterService"]] = relationship(
        "MasterService",
        back_populates="service",
    )
