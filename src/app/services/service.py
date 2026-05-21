from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.service import CRUDService, service_crud
from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceUpdate

from .base import BaseService


class ServiceManager(BaseService[Service, CRUDService]):
    """Сервис для управления услугами салона."""

    model = Service

    def __init__(self, crud: CRUDService) -> None:
        """Инициализирует сервис управления услугами салона."""
        super().__init__(crud)

    async def get_services(
        self,
        session: AsyncSession,
        active: bool = True,
    ) -> list[Service]:
        """Возвращает список услуг (только активные или все)."""
        if active:
            return await self.crud.get_multi(
                session,
                is_active=True,
            )
        return await self.crud.get_multi(session)

    async def create_service(
        self,
        session: AsyncSession,
        request: ServiceCreate,
    ) -> Service:
        """Создаёт новую услугу салона."""
        service = await self.crud.create(request, session)
        logger.info(
            'Создана услуга name={}',
            request.name,
        )
        return service

    async def update_service(
        self,
        session: AsyncSession,
        service_id: int,
        request: ServiceUpdate,
    ) -> Service:
        """Обновляет услугу салона."""
        service = await self.update(session, service_id, request)
        logger.info(
            'Обновлена услуга service_id={}',
            service_id,
        )
        return service


service_manager = ServiceManager(service_crud)
