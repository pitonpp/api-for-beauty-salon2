from fastapi import APIRouter

from app.api.dependencies import AllowUserDI, AppointmentServiceDI, SessionDI
from app.models.appointment import Appointment
from app.schemas.appointment import AppointmentCreate, AppointmentShort

router = APIRouter()


@router.post("{service_id}/appointments", response_model=AppointmentShort)
async def create_appointment(
    session: SessionDI,
    appointment_service: AppointmentServiceDI,
    user: AllowUserDI,
    request: AppointmentCreate,
    service_id: int,
) -> Appointment:
    return await appointment_service.create_appointment(
        request,
        session,
        user,
        service_id,
    )
