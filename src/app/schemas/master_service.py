from datetime import timedelta

from pydantic import BaseModel, ConfigDict

from .master import MasterDB

from .custom_types import Description, Price


class MasterServiceCreate(BaseModel):
    service_id: int
    price: Price
    description: Description
    duration: timedelta

    model_config = ConfigDict(extra="forbid")


class MasterServiceUpdate(BaseModel):
    price: Price | None = None
    description: Description | None = None
    duration: timedelta | None = None
    is_active: bool | None = None

    model_config = ConfigDict(extra="forbid")


class MasterServiceShort(BaseModel):
    id: int
    service_id: int
    service_name: str
    price: int
    description: str
    duration: timedelta

    model_config = ConfigDict(from_attributes=True)


class MasterServiceDB(MasterServiceShort):
    master: MasterDB
    is_active: bool
