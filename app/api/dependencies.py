from http import HTTPStatus
from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, Depends

from app.core.db import get_async_session
from app.crud.client import client_crud
from app.crud.service import service_crud
from app.models.client import Client
from app.models.service import Service


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
