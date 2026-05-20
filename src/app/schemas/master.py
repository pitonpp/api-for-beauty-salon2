"""Pydantic-схемы для мастеров."""

from pydantic import BaseModel, ConfigDict, PositiveInt

from .custom_types import Description


class MasterBase(BaseModel):
    user_id: int


class MasterAdminCreate(MasterBase):
    bio: Description | None = None
    experience: PositiveInt

    model_config = ConfigDict(
        extra="forbid",
    )


class MasterUpdate(BaseModel):
    bio: Description | None = None

    model_config = ConfigDict(
        extra="forbid",
    )


class MasterAdminUpdate(MasterUpdate):
    user_id: int | None = None
    experience: PositiveInt | None = None


class MasterShort(BaseModel):
    id: int
    bio: str | None = None
    experience: PositiveInt

    model_config = ConfigDict(
        from_attributes=True,
    )


class MasterDB(MasterShort):
    user_id: int
