from fastapi import APIRouter

from app.api.dependencies import (
    AllowAdminDI,
    AppointmentServiceDI,
    SessionDI,
)
from app.models.appointment import Appointment
from app.schemas.appointment import (
    AppointmentAdminCreate,
    AppointmentAdminUpdate,
    AppointmentWithRelations,
)

router = APIRouter()


@router.get("/appointments", response_model=list[AppointmentWithRelations])
async def get_appointments(
    session: SessionDI,
    _: AllowAdminDI,
    appointment_service: AppointmentServiceDI,
) -> list[Appointment]:
    return await appointment_service.get_appointments_with_relations(session)


@router.get(
    "/appointments/{appointment_id}", response_model=AppointmentWithRelations
)
async def get_appointment(
    session: SessionDI,
    _: AllowAdminDI,
    appointment_id: int,
    appointment_service: AppointmentServiceDI,
) -> Appointment:
    return await appointment_service.get_appointment_with_relations(
        session,
        appointment_id,
    )


@router.post("/appointments", response_model=AppointmentWithRelations)
async def create_appointment(
    session: SessionDI,
    request: AppointmentAdminCreate,
    _: AllowAdminDI,
    appointment_service: AppointmentServiceDI,
) -> Appointment:
    return await appointment_service.admin_create_appointment(
        request, session
    )


@router.patch(
    "/appointments/{appointment_id}", response_model=AppointmentWithRelations
)
async def update_appointment(
    session: SessionDI,
    appointment_id: int,
    request: AppointmentAdminUpdate,
    appointment_service: AppointmentServiceDI,
    _: AllowAdminDI,
) -> Appointment:
    return await appointment_service.admin_update_appointment(
        request,
        session,
        appointment_id,
    )
