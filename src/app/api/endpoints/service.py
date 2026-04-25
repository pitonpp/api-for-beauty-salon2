from fastapi import APIRouter

from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceDB, ServiceUpdate

from ..dependencies import AllowAdminDI, ServiceManagerDI, SessionDI

router = APIRouter()


@router.get("/", response_model=list[ServiceDB])
async def get_all_services(
    session: SessionDI,
    service_manager: ServiceManagerDI,
    _: AllowAdminDI,
) -> list[Service]:
    return await service_manager.get_multi(session)


@router.get("/{service_id}", response_model=ServiceDB)
async def get_service_by_id(
    session: SessionDI,
    service_manager: ServiceManagerDI,
    service_id: int,
) -> Service:
    return await service_manager.validate_object_id(service_id, session)


@router.post("/", response_model=ServiceDB)
async def create_service(
    session: SessionDI,
    service_manager: ServiceManagerDI,
    _: AllowAdminDI,
    request: ServiceCreate,
) -> Service:
    return await service_manager.create_service(session, request)


@router.patch("/{service_id}", response_model=ServiceDB)
async def update_service(
    session: SessionDI,
    service_manager: ServiceManagerDI,
    _: AllowAdminDI,
    service_id: int,
    request: ServiceUpdate,
) -> Service:
    return await service_manager.update_service(session, service_id, request)
