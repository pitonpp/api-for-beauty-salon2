"""Pydantic-схемы для услуг салона."""

from pydantic import BaseModel, ConfigDict

from .custom_types import Name


class ServiceBase(BaseModel):
    name: Name


class ServiceCreate(ServiceBase):
    model_config = ConfigDict(
        extra="forbid",
    )


class ServiceUpdate(ServiceCreate):
    name: Name | None = None


class ServiceShort(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)
