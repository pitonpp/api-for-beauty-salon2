from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Annotated

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, Depends

from app.core.db import get_async_session
from app.crud import client_crud, service_crud, crud_appointment
from app.models.appointment import Appointment
from app.models.client import Client
from app.models.service import Service
from app.models.appointment import Appointment
from app.schemas.status_enum import AppointmentStatus


SessionDI = Annotated[AsyncSession, Depends(get_async_session)]


async def valid_client_id(client_id: int, session: SessionDI) -> Client:
    client = await client_crud.get(client_id, session)
    if not client:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Клиент c {client_id} не найден",
        )
    return client


ValidClientDI = Annotated[Client, Depends(valid_client_id)]


async def check_unique_phone(phone: str, session: SessionDI) -> None:
    client = await client_crud.get_by_phone(phone, session)
    if client:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Клиент с таким телефоном {phone} уже существует",
        )


async def check_name_service(service_name: str, session: SessionDI) -> None:
    service = await service_crud.get_service_id_by_name(service_name, session)
    if service:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Услуга с таким именем '{service_name}' уже существует",
        )


async def valid_service_id(service_id: int, session: SessionDI) -> Service:
    service = await service_crud.get(service_id, session)
    if not service:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Услуга с ID {service_id} не найдена",
        )
    return service


ValidServiceDI = Annotated[Service, Depends(valid_service_id)]


async def check_time_availiable(
    appointment_time: datetime, session: SessionDI, duration: timedelta
) -> None:
    end_time = appointment_time + duration
    stmt = select(Appointment).where(
        and_(
            Appointment.appointment_time < end_time,
            Appointment.appointment_time + duration > appointment_time,
            Appointment.status == "Запланированная",
        )
    )
    result = await session.execute(stmt)
    if not result:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail="Время записи занято"
        )


async def valid_appointment_id(
    appointment_id: int, session: SessionDI
) -> Appointment:
    appointment = await crud_appointment.get(appointment_id, session)
    if not appointment:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Запись с ID {appointment_id} не найдена",
        )
    return appointment


ValidAppointmentDI = Annotated[Appointment, Depends(valid_appointment_id)]
