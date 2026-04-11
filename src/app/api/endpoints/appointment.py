from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException

from src.app.api.dependencies import (
    SessionDI,
    check_time_availiable,
    get_current_user,
    role_checker,
    valid_appointment_id,
    valid_service_id,
    valid_user_id,
)
from src.app.crud.appointment import crud_appointment
from src.app.models.user import User
from src.app.schemas.appointment import (
    AppointmentAdminUpdate,
    AppointmentCreate,
    AppointmentInDB,
    AppointmentWithRelations,
)
from src.app.schemas.status_enum import UserRole

router = APIRouter()


@router.get(
    "/",
    response_model=list[AppointmentInDB],
    summary="Получить список записей на услуги",
    dependencies=[Depends(role_checker(UserRole.ADMIN))],
)
async def get_appointments(session: SessionDI):
    """Только для админа"""
    appointments = await crud_appointment.get_multi(session)
    return appointments


@router.get(
    "/full_appointments",
    response_model=AppointmentWithRelations,
    summary="Получить полные записи на услуги",
    dependencies=[Depends(role_checker(UserRole.ADMIN))],
)
async def get_appointments_with_relations(session: SessionDI):
    """Только для админа"""
    appointments = await crud_appointment.get_multi_with_relations(session)
    return appointments


@router.post(
    "/", response_model=AppointmentInDB, summary="Создать запись на услугу"
)
async def create_appointment(
    appointment: AppointmentCreate,
    session: SessionDI,
    service_id: int,
    user: User = Depends(get_current_user),
):
    service = await valid_service_id(service_id, session)
    await check_time_availiable(
        appointment.appointment_time, session, service.duration
    )
    appointment_data = appointment.model_dump()
    appointment_data["user_id"] = user.id
    appointment_data["service_id"] = service.id
    new_appointment = await crud_appointment.create_appointment(
        session, appointment_data
    )
    return new_appointment


@router.patch(
    "/{appointment_id}",
    response_model=AppointmentInDB,
    summary="Изменить запись на услугу",
    dependencies=[Depends(role_checker(UserRole.ADMIN))],
)
async def update_appointment(
    appointment_id: int,
    obj_in: AppointmentAdminUpdate,
    session: SessionDI,
):
    """Только для админа"""
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
    user: User = Depends(get_current_user),
):
    appointment = await valid_appointment_id(appointment_id, session)
    if appointment.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="У вас нет прав удалить чужую запись",
        )
    deleted_appointment = await crud_appointment.delete(appointment, session)
    return deleted_appointment
