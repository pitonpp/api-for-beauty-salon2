from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.db import get_async_session
from src.app.core.jwt_services import verify_token
from src.app.crud import crud_appointment, service_crud, user_crud
from src.app.models.appointment import Appointment
from src.app.models.service import Service
from src.app.models.user import User
from src.app.schemas.status_enum import UserRole

SessionDI = Annotated[AsyncSession, Depends(get_async_session)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def valid_user_id(user_id: int, session: SessionDI) -> User:
    user = await user_crud.get(user_id, session)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Пользователь c {user_id} не найден",
        )
    return user


async def check_unique_phone(phone: str, session: SessionDI) -> None:
    user = await user_crud.get_by_phone(session, phone)
    if user:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Пользователь с таким телефоном {phone} уже существует",
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


async def get_current_user(
    session: SessionDI, token: str = Depends(oauth2_scheme)
) -> User:
    token_data = verify_token(token)

    if token_data is None:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Не удалось подтвердить учетные данные",
        )

    user = await user_crud.get(token_data.user_id, session)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Не удалось подтвердить учетные данные",
        )

    if user.is_active is False:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Пользователь забанен"
        )
    return user


def role_checker(required_role: UserRole):
    async def checker(
        user: User = Depends(get_current_user),
    ) -> User:
        if user.role != required_role.value:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN, detail="Здесь ничего нет"
            )
        return user

    return checker
