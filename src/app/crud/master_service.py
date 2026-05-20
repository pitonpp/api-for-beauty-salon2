from sqlalchemy import Select, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.master_service import MasterService
from app.schemas.master_service import (
    MasterServiceCreate,
    MasterServiceUpdate,
)


class CRUDMasterService(
    CRUDBase[
        MasterService,
        MasterServiceCreate,
        MasterServiceUpdate,
    ]
):
    def _get_statement(
        self,
        master_id: int,
        skip: int = 0,
        limit: int = 10,
        service_id: int | None = None,
    ) -> Select:
        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.service),
                selectinload(self.model.master),
            )
            .where(self.model.master_id == master_id)
        )
        if service_id is not None:
            stmt = stmt.where(self.model.service_id == service_id)
        else:
            stmt = stmt.offset(skip).limit(limit).order_by(self.model.id)
        return stmt

    async def _reload_with_relations(
        self,
        obj: MasterService,
        session: AsyncSession,
    ) -> MasterService:
        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.service),
                selectinload(self.model.master),
            )
            .where(self.model.id == obj.id)
        )

        result = await session.execute(stmt)
        return result.scalar_one()

    async def get_master_service(
        self,
        session: AsyncSession,
        master_id: int,
        service_id: int,
    ) -> MasterService | None:
        stmt = self._get_statement(
            master_id=master_id,
            service_id=service_id,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_master_services(
        self,
        session: AsyncSession,
        master_id: int,
        skip: int = 0,
        limit: int = 10,
    ) -> list[MasterService]:
        stmt = self._get_statement(
            master_id=master_id,
            skip=skip,
            limit=limit,
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def create(
        self,
        request: MasterServiceCreate | dict,
        session: AsyncSession,
    ) -> MasterService:
        obj = await super().create(request, session)
        return await self._reload_with_relations(obj, session)

    async def update(
        self,
        db_obj: MasterService,
        request: MasterServiceUpdate | dict,
        session: AsyncSession,
    ) -> MasterService:
        obj = await super().update(db_obj, request, session)
        return await self._reload_with_relations(obj, session)


master_service_crud = CRUDMasterService(MasterService)
