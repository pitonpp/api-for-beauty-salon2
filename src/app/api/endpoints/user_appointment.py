from fastapi import APIRouter

from app.api.dependencies import AllowUserDI, AppointmentServiceDI, SessionDI
from app.models.appointment import Appointment
from app.schemas.appointment import AppointmentShort, AppointmentUpdate

router = APIRouter()


@router.get(
    "/me/appointmets",
    response_model=AppointmentShort,
)
async def get_appointments(
    session: SessionDI,
    appointment_serivce: AppointmentServiceDI,
    user: AllowUserDI,
) -> list[Appointment]:
    return await appointment_serivce.get_user_appointments(session, user)


@router.get(
    "/me/appointments/{appointment_id}",
    response_model=AppointmentShort,
)
async def get_appointment(
    session: SessionDI,
    appointment_service: AppointmentServiceDI,
    user: AllowUserDI,
    appointment_id: int,
) -> Appointment:
    return await appointment_service.get_user_appointment(
        session,
        user,
        appointment_id,
    )


@router.patch(
    "/me/appointments/{appointment_id}",
    response_model=AppointmentShort,
)
async def update_appointment(
    session: SessionDI,
    appointment_id: int,
    appointment_service: AppointmentServiceDI,
    request: AppointmentUpdate,
    user: AllowUserDI,
) -> Appointment:
    return await appointment_service.update_appointment(
        request,
        session,
        appointment_id,
        user,
    )
