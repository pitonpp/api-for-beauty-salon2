from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.master import CRUDMaster, master_crud
from app.models.master import Master
from app.models.user import User
from app.schemas.master import (
    MasterAdminCreate,
    MasterAdminUpdate,
    MasterUpdate,
)
from app.schemas.status_enum import UserRole
from app.services.user import user_service

from .base import BaseService


class MasterManager(BaseService[Master, CRUDMaster]):
    model = Master

    def __init__(self, crud: CRUDMaster) -> None:
        super().__init__(crud)
        self.user_service = user_service

    async def _change_role(
        self,
        session: AsyncSession,
        user: User,
    ) -> None:
        user.role = UserRole.MASTER
        await session.commit()

    async def create_master(
        self,
        session: AsyncSession,
        request: MasterAdminCreate,
    ) -> Master:
        user = await self.user_service.get_object_or_404(
            request.user_id, session
        )
        master = await self.create(request, session)
        await self._change_role(session, user)
        return master

    async def update_master(
        self,
        session: AsyncSession,
        user: User,
        request: MasterAdminUpdate | MasterUpdate,
    ) -> Master:
        master = await self.get_master_by_user_id(session, user)
        return await self.update(session, master.id, request)

    async def downgrade_role(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> User:
        user = await self.user_service.get_object_or_404(user_id, session)
        if user.role == UserRole.MASTER:
            user.role = UserRole.USER
            await session.commit()
        return user

    async def get_masters(
        self,
        session: AsyncSession,
    ) -> list[Master]:
        return await self.crud.get_multi(session)

    async def get_master(
        self,
        session: AsyncSession,
        master_id: int,
    ) -> Master:
        return await self.get_object_or_404(master_id, session)

    async def get_master_by_user_id(
        self,
        session: AsyncSession,
        user: User,
    ) -> Master:
        master = await self.crud.get_one_by(session, user_id=user.id)
        if master is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Вы не являетесь мастером",
            )
        if user.role != UserRole.MASTER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Вы не являетесь мастером",
            )
        return master


master_manager = MasterManager(master_crud)
