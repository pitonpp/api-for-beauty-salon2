"""Pydantic-схемы для мастеров."""

from pydantic import BaseModel, ConfigDict, PositiveInt

from .custom_types import Description


class MasterBase(BaseModel):
    """Базовая схема мастера."""

    user_id: int


class MasterAdminCreate(MasterBase):
    """Схема создания мастера администратором."""

    bio: Description | None = None
    experience: PositiveInt

    model_config = ConfigDict(
        extra='forbid',
    )


class MasterUpdate(BaseModel):
    """Схема обновления мастера."""

    bio: Description | None = None

    model_config = ConfigDict(
        extra='forbid',
    )


class MasterAdminUpdate(MasterUpdate):
    """Схема обновления мастера администратором."""

    user_id: int | None = None
    experience: PositiveInt | None = None


class MasterShort(BaseModel):
    """Краткая схема мастера."""

    id: int
    bio: str | None = None
    experience: PositiveInt

    model_config = ConfigDict(
        from_attributes=True,
    )


class MasterDB(MasterShort):
    """Полная схема мастера из БД."""

    user_id: int
