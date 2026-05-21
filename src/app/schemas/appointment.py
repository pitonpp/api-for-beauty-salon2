"""Pydantic-схемы для записей (создание, обновление, отображение)."""

from datetime import datetime, timedelta, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.master import MasterShort
from app.schemas.master_service import MasterServiceShort

from .status_enum import AppointmentStatus
from .user import UserShort

TIME_EXAMPLE = (
    (datetime.now(timezone.utc) + timedelta(hours=1))
    .replace(second=0, microsecond=0)
    .isoformat(timespec='minutes')
)


class AppointmentBase(BaseModel):
    """Базовая схема записи."""

    appointment_time: datetime = Field(
        ...,
        description='Время записи',
        examples=[TIME_EXAMPLE],
    )


class AppointmentCreate(AppointmentBase):
    """Схема создания записи пользователем."""


class AppointmentAdminCreate(AppointmentCreate):
    """Схема создания записи администратором."""

    master_service_id: int
    user_id: int


class AppointmentAdminUpdate(AppointmentCreate):
    """Схема обновления записи администратором."""

    appointment_time: datetime | None = None
    master_service_id: int | None = None
    status: AppointmentStatus | None = AppointmentStatus.SCHEDULED


class AppointmentUpdate(AppointmentCreate):
    """Схема обновления записи пользователем."""

    appointment_time: datetime | None = None
    status: Literal[AppointmentStatus.CANCELED] | None = Field(
        None,
        description='Пользователь может только отменить запись',
    )


class AppointmentMasterUpdate(BaseModel):
    """Схема обновления записи мастером."""

    status: Literal[AppointmentStatus.COMPLETED] | None = Field(
        None,
        description='Мастер может завершить запись',
    )


class AppointmentShort(AppointmentBase):
    """Краткая схема записи для списка."""

    id: int
    service_name: str
    status: AppointmentStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AppointmentDB(AppointmentShort):
    """Полная схема записи из БД."""

    client_id: int
    master_service_id: int


class AppointmentWithRelationsMaster(AppointmentBase):
    """Схема записи со связанными данными (без мастера)."""

    id: int
    status: AppointmentStatus
    user: UserShort
    master_service: MasterServiceShort
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AppointmentWithRelations(AppointmentWithRelationsMaster):
    """Схема записи с мастером."""

    master: MasterShort
