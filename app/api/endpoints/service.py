from fastapi import APIRouter

from app.crud.service import service_crud
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceDB
from app.api.dependencies import SessionDI, ValidServiceDI, check_name_service

router = APIRouter()


@router.get(
    "/",
    response_model=List[ServiceDB],
    summary="Получить список услуг",
)
async def get_services(session: SessionDI):
    services = await service_crud.get_multi(session)
    return services


@router.post(
    "/",
    response_model=ServiceDB,
    summary="Создать новую услугу",
)
async def create_service(service: ServiceCreate, session: SessionDI):
    await check_name_service(service.name, session)
    new_service = await service_crud.create(service, session)
    return new_service


@router.patch(
    "/{service_id}",
    response_model="ServiceDB",
    summary="Обновить данные услуги",
)
async def update_service(
    service: ValidServiceDI,
    obj_in: ServiceUpdate,
    session: SessionDI,
):
    if obj_in.name is not None:
        await check_name_service(obj_in.name, session)

    service = await service_crud.update(service, obj_in, session)
    return service


@router.delete(
    "/{service_id}",
    response_model=ServiceDB,
    summary="Удалить услугу",
)
async def delete_service(service: ValidServiceDI, session: SessionDI):
    service = await service_crud.delete(service, session)
    return service
