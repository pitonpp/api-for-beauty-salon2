from datetime import timedelta
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from .custom_types import Name, Price, Description


class ServiceBase(BaseModel):
    name: Name
    price: Price
    duration: timedelta
    description: Description


class ServiceCreate(ServiceBase):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class ServiceUpdate(ServiceCreate):
    name: Name | None = None
    price: Price | None = None
    duration: timedelta | None = None
    description: Description | None = None


class ServiceShort(BaseModel):
    id: int
    name: str
    price: Decimal


class ServiceDB(ServiceShort):
    duration: timedelta
    description: str
