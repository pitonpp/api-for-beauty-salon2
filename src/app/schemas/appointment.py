from datetime import datetime, timedelta, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .service import ServiceShort
from .status_enum import AppointmentStatus
from .user import UserShort

TIME_EXAMPLE = (
    (datetime.now(timezone.utc) + timedelta(hours=1))
    .replace(second=0, microsecond=0)
    .isoformat(timespec="minutes")
)


class AppointmentBase(BaseModel):
    appointment_time: datetime = Field(
        ..., description="Время записи", examples=[TIME_EXAMPLE]
    )


class AppointmentCreate(AppointmentBase):
    model_config = ConfigDict(extra="forbid")


class AppointmentAdminUpdate(AppointmentCreate):
    status: AppointmentStatus | None = AppointmentStatus.SCHEDULED


class AppointmentUpdate(AppointmentCreate):
    appointment_time: datetime | None = None
    status: Literal[AppointmentStatus.CANCELED] | None = Field(
        None,
        description="Пользователь может только отменить запись",
    )


class AppointmentInDB(AppointmentBase):
    id: int
    client_id: int
    service_id: int
    status: str
    created_at: datetime


class AppointmentWithRelations(BaseModel):
    id: int
    appointment_time: datetime
    status: str
    client: UserShort
    service: ServiceShort
