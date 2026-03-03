from fastapi import APIRouter

from app.crud.appointment import crud_appointment
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentInDB,
    AppointmentWithRelations,
)
from app.api.dependencies import (
    SessionDI,
    ValidClientDI,
    ValidServiceDI,
    check_time_availiable,
    ValidAppointmentDI,
    valid_client_id,
    valid_service_id,
)

router = APIRouter()


@router.get(
    "/",
    response_model=list[AppointmentInDB],
    summary="Получить список записей на услуги",
)
async def get_appointments(session: SessionDI):
    appointments = await crud_appointment.get_multi(session)
    return appointments


@router.post(
    "/", response_model=AppointmentInDB, summary="Создать запись на услугу"
)
async def create_appointment(
    appointment: AppointmentCreate,
    session: SessionDI,
    client: ValidClientDI,
    service: ValidServiceDI,
):
    await check_time_availiable(
        appointment.appointment_time, session, service.duration
    )
    appointment_data = appointment.model_dump()
    appointment_data["client_id"] = client.id
    appointment_data["service_id"] = service.id
    new_appointment = await crud_appointment.create_appointment(
        session, appointment_data
    )
    return new_appointment


@router.patch(
    "/{appointment_id}",
    response_model=AppointmentInDB,
    summary="Изменить запись на услугу",
)
async def update_appointment(
    appointment: ValidAppointmentDI,
    obj_in: AppointmentUpdate,
    session: SessionDI,
):
    if obj_in.appointment_time:
        await check_time_availiable(
            obj_in.appointment_time, session, appointment.service.duration
        )

    if obj_in.client_id:
        await valid_client_id(obj_in.client_id, session)

    if obj_in.service_id:
        await valid_service_id(obj_in.service_id, session)

    updated_appointment = await crud_appointment.update(
        appointment, obj_in, session
    )
    return updated_appointment


@router.delete(
    "/{appointment_id}",
    response_model=AppointmentInDB,
    summary="Удалить запись на услугу",
)
async def delete_appointment(
    appointment: ValidAppointmentDI,
    session: SessionDI,
):
    deleted_appointment = await crud_appointment.delete(appointment, session)
    return deleted_appointment
