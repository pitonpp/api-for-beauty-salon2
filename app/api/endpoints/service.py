from http import HTTPStatus

from fastapi import APIRouter, Depends

from app.api.dependencies import (
    SessionDI,
    check_name_service,
    role_checker,
    valid_service_id,
)
from app.crud.service import service_crud
from app.models.user import User
from app.schemas.service import ServiceCreate, ServiceDB, ServiceUpdate
from app.schemas.status_enum import UserRole

router = APIRouter()


@router.get(
    "/",
    response_model=list[ServiceDB],
    summary="Получить список услуг",
)
async def get_services(session: SessionDI):
    services = await service_crud.get_multi(session)
    return services


@router.post(
    "/",
    response_model=ServiceDB,
    summary="Создать новую услугу",
    status_code=HTTPStatus.CREATED,
)
async def create_service(
    service: ServiceCreate,
    session: SessionDI,
    user_role: User = Depends(role_checker(UserRole.ADMIN)),
):
    """Только для админа"""
    await check_name_service(service.name, session)
    new_service = await service_crud.create(service, session)
    return new_service


@router.patch(
    "/{service_id}",
    response_model=ServiceDB,
    summary="Обновить данные услуги",
)
async def update_service(
    service_id: int,
    obj_in: ServiceUpdate,
    session: SessionDI,
    user_role: User = Depends(role_checker(UserRole.ADMIN)),
):
    """Только для админа"""
    service = await valid_service_id(service_id, session)

    if obj_in.name is not None:
        await check_name_service(obj_in.name, session)

    service = await service_crud.update(service, obj_in, session)
    return service


@router.delete(
    "/{service_id}",
    response_model=ServiceDB,
    summary="Удалить услугу",
)
async def delete_service(
    service_id: int,
    session: SessionDI,
    user_role: User = Depends(role_checker(UserRole.ADMIN)),
):
    """Только для админа"""
    service = await valid_service_id(service_id, session)
    service = await service_crud.delete(service, session)
    return service
