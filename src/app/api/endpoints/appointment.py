"""Endpoint'ы для создания записей клиентами."""

from fastapi import APIRouter

from app.api.dependencies import (
    AllowUserDI,
    AppointmentServiceDI,
    SessionDI,
    to_schema,
)
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentShort,
)

router = APIRouter()


@router.post("/{master_service_id}", response_model=AppointmentShort)
async def create_appointment(
    master_service_id: int,
    session: SessionDI,
    appointment_service: AppointmentServiceDI,
    user: AllowUserDI,
    request: AppointmentCreate,
) -> AppointmentShort:
    appointment = await appointment_service.create_appointment(
        request,
        session,
        user,
        master_service_id,
    )
    return to_schema(appointment, AppointmentShort)
