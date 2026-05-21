"""Pydantic-схемы для услуг мастера."""

from datetime import timedelta

from pydantic import BaseModel, ConfigDict

from .custom_types import Description, Price
from .master import MasterDB


class MasterServiceCreate(BaseModel):
    """Схема создания услуги мастера."""

    service_id: int
    price: Price
    description: Description
    duration: timedelta

    model_config = ConfigDict(extra="forbid")


class MasterServiceUpdate(BaseModel):
    """Схема обновления услуги мастера."""

    price: Price | None = None
    description: Description | None = None
    duration: timedelta | None = None
    is_active: bool | None = None

    model_config = ConfigDict(extra="forbid")


class MasterServiceShort(BaseModel):
    """Краткая схема услуги мастера."""

    id: int
    service_id: int
    service_name: str
    price: int
    description: str
    duration: timedelta

    model_config = ConfigDict(from_attributes=True)


class MasterServiceDB(MasterServiceShort):
    """Полная схема услуги мастера из БД."""

    master: MasterDB
    is_active: bool
