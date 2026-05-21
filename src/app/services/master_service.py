from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import (
    CANNOT_CHANGE_OTHERS_SERVICE,
    MASTER_ALREADY_HAS_SERVICE,
    MASTER_SERVICE_NOT_FOUND,
)
from app.crud.master_service import CRUDMasterService, master_service_crud
from app.models.master_service import MasterService
from app.models.user import User
from app.schemas.master_service import (
    MasterServiceCreate,
    MasterServiceUpdate,
)
from app.schemas.status_enum import UserRole
from app.services.master import master_manager
from app.services.service import service_manager

from .base import BaseService


class MasterServiceManager(BaseService[MasterService, CRUDMasterService]):
    """Сервис для управления услугами мастеров."""

    model = MasterService

    def __init__(self, crud: CRUDMasterService) -> None:
        """Инициализирует сервис управления услугами мастеров."""
        super().__init__(crud)
        self.service_manager = service_manager
        self.master_manager = master_manager

    async def _check_uniqueness(
        self,
        session: AsyncSession,
        service_id: int,
        master_id: int,
        exclude_id: int | None = None,
    ) -> None:
        """Проверяет, что у мастера ещё нет такой услуги."""
        stmt = select(self.model).where(
            self.model.service_id == service_id,
            self.model.master_id == master_id,
        )
        if exclude_id is not None:
            stmt = stmt.where(self.model.id != exclude_id)

        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            logger.warning(
                "У мастера master_id={} уже есть услуга service_id={}",
                master_id,
                service_id,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=MASTER_ALREADY_HAS_SERVICE,
            )

    async def validate_create_common(
        self,
        session: AsyncSession,
        service_id: int,
        master_id: int,
        master_check: bool = False,
    ) -> None:
        """Валидирует уникальность и существование услуги/мастера."""
        await self._check_uniqueness(
            session,
            service_id,
            master_id,
        )
        await self.service_manager.get_object_or_404(
            service_id,
            session,
        )

        if master_check:
            await self.master_manager.get_object_or_404(
                master_id,
                session,
            )

    async def create_master_service(
        self,
        session: AsyncSession,
        request: MasterServiceCreate,
        user: User,
    ) -> MasterService:
        """Создаёт услугу для текущего мастера (из контекста)."""
        master = await self.master_manager.get_master_by_user_id(
            session,
            user,
        )
        await self.validate_create_common(
            session,
            request.service_id,
            master.id,
        )
        request_data = request.model_dump()
        request_data["master_id"] = master.id
        master_service = await self.create(
            request_data,
            session,
        )

        logger.info(
            "Создана услуга master_service_id={} для master_id={} "
            "service_id={}",
            master_service.id,
            master.id,
            request.service_id,
        )
        return master_service

    async def create_master_service_admin(
        self,
        session: AsyncSession,
        request: MasterServiceCreate,
        master_id: int,
    ) -> MasterService:
        """Создаёт услугу для указанного мастера (администратором)."""
        request_data = request.model_dump()
        request_data["master_id"] = master_id
        await self.validate_create_common(
            session,
            request_data["service_id"],
            master_id,
            True,
        )
        master_service = await self.create(
            request_data,
            session,
        )
        logger.info(
            "Создана услуга master_service_id={} для master_id={} "
            "service_id={}",
            master_service.id,
            master_id,
            request_data["service_id"],
        )
        return master_service

    async def update_master_service(
        self,
        session: AsyncSession,
        master_service_id: int,
        request: MasterServiceUpdate,
        user: User,
        master_id: int | None = None,
    ) -> MasterService:
        """Обновляет услугу мастера (с проверкой прав)."""
        if master_id:
            master = await self.master_manager.get_master(
                session,
                master_id,
            )

        else:
            master = await self.master_manager.get_master_by_user_id(
                session,
                user,
            )

        master_service = await self.get_object_or_404(
            master_service_id,
            session,
        )

        if (
            user.role != UserRole.ADMIN
            and master_service.master_id != master.id
        ):
            logger.warning(
                "Попытка изменить чужую услугу master_service_id={}: "
                "user_id={}, username={}",
                master_service_id,
                user.id,
                user.username,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=CANNOT_CHANGE_OTHERS_SERVICE,
            )

        updated = await self.update(
            session,
            master_service_id,
            request,
            master_service,
        )
        logger.info(
            "Изменена услуга master_service_id={}",
            master_service_id,
        )
        return updated

    async def get_master_services(
        self,
        session: AsyncSession,
        master_id: int,
    ) -> list[MasterService]:
        """Возвращает услуги мастера."""
        await self.master_manager.get_object_or_404(
            master_id,
            session,
        )
        return await self.crud.get_master_services(
            session,
            master_id,
        )

    async def get_master_service(
        self,
        session: AsyncSession,
        master_id: int,
        service_id: int,
    ) -> MasterService:
        """Возвращает конкретную услугу мастера (по service_id)."""
        await self.master_manager.get_object_or_404(
            master_id,
            session,
        )
        service = await self.crud.get_master_service(
            session,
            master_id,
            service_id,
        )

        if service is None:
            logger.warning(
                "Услуга service_id={} мастера master_id={} не найдена",
                service_id,
                master_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MASTER_SERVICE_NOT_FOUND,
            )

        return service

    async def get_my_services(
        self,
        session: AsyncSession,
        user: User,
    ) -> list[MasterService]:
        """Возвращает услуги текущего мастера."""
        master = await self.master_manager.get_master_by_user_id(
            session,
            user,
        )
        return await self.crud.get_master_services(
            session,
            master.id,
        )

    async def get_my_service(
        self,
        session: AsyncSession,
        user: User,
        service_id: int,
    ) -> MasterService:
        """Возвращает конкретную услугу текущего мастера."""
        master = await self.master_manager.get_master_by_user_id(
            session,
            user,
        )
        service = await self.crud.get_master_service(
            session,
            master.id,
            service_id,
        )

        if service is None:
            logger.warning(
                "Услуга service_id={} мастера master_id={} не найдена",
                service_id,
                master.id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MASTER_SERVICE_NOT_FOUND,
            )

        return service


master_service_manager = MasterServiceManager(master_service_crud)
