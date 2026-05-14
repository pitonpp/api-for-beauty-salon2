from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
    model = MasterService

    def __init__(self, crud: CRUDMasterService) -> None:
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
        stmt = select(self.model).where(
            self.model.service_id == service_id,
            self.model.master_id == master_id,
        )
        if exclude_id is not None:
            stmt = stmt.where(self.model.id != exclude_id)

        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="У этого мастера уже есть такая услуга",
            )

    async def validate_create_common(
        self,
        session: AsyncSession,
        service_id: int,
        master_id: int,
        master_check: bool = False,
    ) -> None:
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
        master = await self.master_manager.get_master_by_user_id(
            session,
            user,
        )
        await self.validate_create_common(
            session,
            request.service_id,
            master.id,
        )
        return await self.create(
            request,
            session,
        )

    async def create_master_service_admin(
        self,
        session: AsyncSession,
        request: MasterServiceCreate,
        master_id: int,
    ) -> MasterService:
        request_data = request.model_dump()
        request_data["master_id"] = master_id
        await self.validate_create_common(
            session,
            request_data["service_id"],
            master_id,
            True,
        )
        return await self.create(
            request_data,
            session,
        )

    async def update_master_service(
        self,
        session: AsyncSession,
        master_service_id: int,
        request: MasterServiceUpdate,
        user: User,
        master_id: int | None = None,
    ) -> MasterService:

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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нельзя менять чужую услугу",
            )

        return await self.update(
            session,
            master_service_id,
            request,
            master_service,
        )

    async def get_master_services(
        self,
        session: AsyncSession,
        master_id: int,
    ) -> list[MasterService]:
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
            raise HTTPException(
                status_code=404, detail="Услуга мастера не найдена"
            )
        return service

    async def get_my_services(
        self,
        session: AsyncSession,
        user: User,
    ) -> list[MasterService]:
        master = await self.master_manager.get_master_by_user_id(
            session,
            user,
        )
        services = await self.crud.get_master_services(
            session,
            master.id,
        )
        return services

    async def get_my_service(
        self,
        session: AsyncSession,
        user: User,
        service_id: int,
    ) -> MasterService:
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
            raise HTTPException(
                status_code=404,
                detail="Услуга мастера не найдена",
            )
        return service


master_service_manager = MasterServiceManager(master_service_crud)
