"""Pydantic-схемы для услуг салона."""

from pydantic import BaseModel, ConfigDict

from .custom_types import Name


class ServiceBase(BaseModel):
    """Базовая схема услуги."""

    name: Name


class ServiceCreate(ServiceBase):
    """Схема создания услуги."""

    model_config = ConfigDict(
        extra="forbid",
    )


class ServiceUpdate(ServiceCreate):
    """Схема обновления услуги."""

    name: Name | None = None


class ServiceShort(BaseModel):
    """Краткая схема услуги."""

    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)
