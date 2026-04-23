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

    async def create_service(
        self, session: AsyncSession, request: ServiceCreate
    ) -> Service:
        try:
            return await self.crud.create(request, session)

        except IntegrityError as e:
            await session.rollback()
            self._handle_integrity_error(e, "create")

    async def update_service(
        self, session: AsyncSession, service_id: int, request: ServiceUpdate
    ) -> Service:
        try:
            service = await self.validate_object_id(service_id, session)
            return await self.crud.update(service, request, session)

        except IntegrityError as e:
            await session.rollback()
            self._handle_integrity_error(e, "update")


service_manager = ServiceManager(service_crud)
