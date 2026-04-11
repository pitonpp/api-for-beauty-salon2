from datetime import datetime
import uuid

from src.app.core.db import Base, CommonBaseMixin
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import (
    UUID,
    Boolean,
    DateTime,
    Integer,
    String,
    ForeignKey,
    text,
)


class RefreshToken(CommonBaseMixin, Base):
    jti: Mapped[uuid.UUID] = mapped_column(
        UUID,
        unique=True,
        index=True,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), index=True
    )
    token_hash: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )
    revoked: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
