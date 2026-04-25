from datetime import datetime, timedelta, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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


class AppointmentAdminCreate(AppointmentCreate):
    service_id: int
    user_id: int


class AppointmentAdminUpdate(AppointmentCreate):
    appointment_time: datetime | None = None
    service_id: int | None = None
    status: AppointmentStatus | None = AppointmentStatus.SCHEDULED


class AppointmentUpdate(AppointmentCreate):
    appointment_time: datetime | None = None
    status: Literal[AppointmentStatus.CANCELED] | None = Field(
        None,
        description="Пользователь может только отменить запись",
    )


class AppointmentShort(AppointmentBase):
    service_name: str
    status: AppointmentStatus
    created_at: datetime


class AppointmentInDB(AppointmentShort):
    id: int
    client_id: int
    service_id: int


class AppointmentWithRelations(BaseModel):
    id: int
    appointment_time: datetime
    status: AppointmentStatus
    client: UserShort
    service: ServiceShort
    created_at: datetime
