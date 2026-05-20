"""Публичные endpoint'ы для просмотра услуг салона."""

from fastapi import APIRouter

from app.schemas.service import (
    ServiceShort,
)

from ..dependencies import (
    ServiceManagerDI,
    SessionDI,
    to_schema,
    to_schema_list,
)

router = APIRouter()


@router.get("", response_model=list[ServiceShort])
async def get_services(
    session: SessionDI,
    service_manager: ServiceManagerDI,
) -> list[ServiceShort]:
    services = await service_manager.get_services(session)
    return to_schema_list(services, ServiceShort)


@router.get("/{service_id}", response_model=ServiceShort)
async def get_service(
    session: SessionDI,
    service_manager: ServiceManagerDI,
    service_id: int,
) -> ServiceShort:
    service = await service_manager.get_object_or_404(service_id, session)
    return to_schema(service, ServiceShort)
