from fastapi import APIRouter

from app.api.dependencies import (
    SessionDI,
    check_time_availiable,
    valid_appointment_id,
    valid_service_id,
    valid_user_id,
)
from app.crud.appointment import crud_appointment
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentInDB,
    AppointmentUpdate,
    AppointmentWithRelations,
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


@router.get(
    "/",
    response_model=AppointmentWithRelations,
    summary="Получить полные записи на услуги",
)
async def get_appointments_with_relations(session: SessionDI):
    appointments = await crud_appointment.get_multi_with_relations(session)
    return appointments


@router.post(
    "/", response_model=AppointmentInDB, summary="Создать запись на услугу"
)
async def create_appointment(
    appointment: AppointmentCreate,
    session: SessionDI,
    client_id: int,
    service_id: int,
):
    service = await valid_service_id(service_id, session)
    client = await valid_user_id(client_id, session)
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
    appointment_id: int,
    obj_in: AppointmentUpdate,
    session: SessionDI,
):
    appointment = await valid_appointment_id(appointment_id, session)
    service_id = appointment.service_id
    service = await valid_service_id(service_id, session)

    if obj_in.appointment_time:
        await check_time_availiable(
            obj_in.appointment_time, session, service.duration
        )

    if obj_in.client_id:
        await valid_user_id(obj_in.client_id, session)

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
    appointment_id: int,
    session: SessionDI,
):
    appointment = await valid_appointment_id(appointment_id, session)
    deleted_appointment = await crud_appointment.delete(appointment, session)
    return deleted_appointment
