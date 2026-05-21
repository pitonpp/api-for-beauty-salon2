import uuid
from datetime import datetime

from sqlalchemy import (
    UUID,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, CommonBaseMixin


class RefreshToken(CommonBaseMixin, Base):
    """Модель refresh-токена для управления сессиями."""

    jti: Mapped[uuid.UUID] = mapped_column(
        UUID,
        unique=True,
        index=True,
        nullable=False,
        comment="Уникальный идентификатор токена",
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), index=True, comment="ID пользователя",
    )
    token_hash: Mapped[str] = mapped_column(
        String, unique=True, nullable=True, comment="Хэш токена",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), comment="Время истечения токена",
    )
    revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        comment="Отозван ли токен",
    )
