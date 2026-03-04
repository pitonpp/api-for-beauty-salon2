from datetime import datetime, timedelta, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.user import UserShort
from app.schemas.service import ServiceShort
from app.schemas.status_enum import AppointmentStatus

TIME_EXAMPLE = (
    (datetime.now(timezone.utc) + timedelta(hours=1))
    .replace(second=0, microsecond=0)
    .isoformat(timespec="minutes")
)


def validate_future(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return value

    if value <= datetime.now(timezone.utc):
        raise ValueError("Запись должна быть в будущем времени")
    return value


class AppointmentBase(BaseModel):
    appointment_time: datetime = Field(
        ..., description="Время записи", examples=[TIME_EXAMPLE]
    )

    model_config = ConfigDict(from_attributes=True)


class AppointmentCreate(AppointmentBase):
    @field_validator("appointment_time")
    def check_future(cls, value):
        return validate_future(value)


class AppointmentUpdate(BaseModel):
    appointment_time: Optional[datetime] = None
    client_id: Optional[int] = None
    service_id: Optional[int] = None
    status: Optional[AppointmentStatus] = AppointmentStatus.SCHEDULED

    @field_validator("appointment_time")
    def check_future(cls, value):
        return validate_future(value)

    @field_validator("status")
    def check_status(cls, value):
        if value is not None:
            if value not in AppointmentStatus:
                raise ValueError("Недопустимое значение статуса")
        return value

    model_config = ConfigDict(from_attributes=True)


class AppointmentInDB(AppointmentBase):
    id: int
    client_id: int
    service_id: int
    status: str


class AppointmentWithRelations(BaseModel):
    id: int
    appointment_time: datetime
    status: str
    client: UserShort
    service: ServiceShort
