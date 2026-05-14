from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.service import CRUDService, service_crud
from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceUpdate

from .base import BaseService


class ServiceManager(BaseService[Service, CRUDService]):
    model = Service

    def __init__(self, crud: CRUDService):
        super().__init__(crud)

    async def get_services(
        self,
        session: AsyncSession,
        active: bool = True,
    ) -> list[Service]:
        if active:
            return await self.crud.get_multi(
                session,
                is_active=True,
            )
        return await self.crud.get_multi(session)

    async def create_service(
        self, session: AsyncSession, request: ServiceCreate
    ) -> Service:
        return await self.crud.create(request, session)

    async def update_service(
        self, session: AsyncSession, service_id: int, request: ServiceUpdate
    ) -> Service:
        return await self.update(session, service_id, request)


service_manager = ServiceManager(service_crud)
