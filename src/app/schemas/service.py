from datetime import timedelta

from pydantic import BaseModel, ConfigDict, Field, PositiveInt


class ServiceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: PositiveInt
    duration: timedelta

    model_config = ConfigDict(from_attributes=True)


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(ServiceBase):
    name: str | None = None
    price: PositiveInt | None = None
    duration: timedelta | None = None


class ServiceDB(ServiceBase):
    id: int


class ServiceShort(BaseModel):
    id: int
    name: str
    price: PositiveInt
