from datetime import timedelta
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, PositiveInt

from app.schemas.appointment import AppointmentInDB


class ServiceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: PositiveInt
    duration: timedelta

    model_config = ConfigDict(from_attributes=True)


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(ServiceBase):
    name: Optional[str] = None
    price: Optional[PositiveInt] = None
    duration: Optional[timedelta] = None


class ServiceDB(ServiceBase):
    id: int
    appointments: Optional[list[AppointmentInDB]] = None


class ServiceShort(BaseModel):
    id: int
    name = str
    price = PositiveInt
