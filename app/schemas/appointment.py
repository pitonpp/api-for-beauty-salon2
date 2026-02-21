from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


TIME_EXAMPLE = (
    (datetime.now() + timedelta(hours=1))
    .replace(second=0, microsecond=0)
    .isoformat(timespec="minutes")
)


def validate_future(value: datetime) -> datetime:
    if value is None:
        return value

    if value < datetime.now():
        raise ValueError("Запись должна быть в будущем времени")
    return value


class AppointmentBase(BaseModel):
    appointment_time: datetime = Field(
        ..., description="Время записи", examples=[TIME_EXAMPLE]
    )
    client_id: int
    service_id: int

    model_config = ConfigDict(from_attributes=True)


class AppointmentCreate(AppointmentBase):
    @field_validator("appointment_time")
    def check_future(cls, value):
        return validate_future(value)


class AppointmentUpdate(BaseModel):
    appointment_time: Optional[datetime] = None
    client_id: Optional[int] = None
    service_id: Optional[int] = None
    status: Optional[str] = None

    @field_validator("appointment_time")
    def check_future(cls, value):
        return validate_future(value)

    model_config = ConfigDict(from_attributes=True)


class AppointmentInDB(AppointmentBase):
    id: int
    status: str
