from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import ALREADY_A_MASTER, MISSING_MASTER_ID, NOT_A_MASTER
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
    """Сервис для управления мастерами и их ролями."""

    model = Master

    def __init__(self, crud: CRUDMaster) -> None:
        """Инициализирует сервис управления мастерами."""
        super().__init__(crud)
        self.user_service = user_service

    async def _change_role(
        self,
        session: AsyncSession,
        user: User,
    ) -> None:
        """Меняет роль пользователя на MASTER."""
        user.role = UserRole.MASTER
        logger.info(
            'Изменилась роль у пользователя username={}, role={}',
            user.username,
            user.role,
        )
        await session.commit()

    async def create_master(
        self,
        session: AsyncSession,
        request: MasterAdminCreate,
    ) -> Master:
        """Создаёт мастера и меняет роль пользователя на MASTER."""
        user = await self.user_service.get_object_or_404(
            request.user_id,
            session,
        )
        if user.role == UserRole.MASTER:
            logger.warning(
                'Попытка создать мастера с уже существующим user_id={}',
                user.id,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ALREADY_A_MASTER,
            )

        master = await self.create(request, session)
        await self._change_role(session, user)
        logger.info(
            'Создан мастер: master_id={}, user_id={}',
            master.id,
            user.id,
        )
        return master

    async def update_master(
        self,
        session: AsyncSession,
        request: MasterAdminUpdate | MasterUpdate,
        user: User,
        master_id: int | None = None,
    ) -> Master:
        """Обновляет данные мастера (по user_id)."""
        if user.role == UserRole.ADMIN:
            if master_id is None:
                logger.warning('В запросе отсутствует master_id')
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=MISSING_MASTER_ID,
                )
            master = await self.get_object_or_404(master_id, session)
        else:
            master = await self.get_master_by_user_id(session, user)

        updated = await self.update(session, master.id, request)
        logger.info('Мастер master_id={} обновлен', master.id)
        return updated

    async def downgrade_role(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> User:
        """Понижает роль мастера до обычного пользователя."""
        user = await self.user_service.get_object_or_404(user_id, session)
        if user.role == UserRole.MASTER:
            user.role = UserRole.USER
            await session.commit()
            logger.info(
                'Роль мастера user_id={} username={} понижена до USER',
                user_id,
                user.username,
            )
        return user

    async def get_masters(
        self,
        session: AsyncSession,
    ) -> list[Master]:
        """Возвращает всех мастеров."""
        return await self.crud.get_multi(session)

    async def get_master(
        self,
        session: AsyncSession,
        master_id: int,
    ) -> Master:
        """Возвращает мастера по ID или 404."""
        return await self.get_object_or_404(master_id, session)

    async def get_master_by_user_id(
        self,
        session: AsyncSession,
        user: User,
    ) -> Master:
        """Возвращает мастера по user_id или 400, если не мастер."""
        master = await self.crud.get_one_by(session, user_id=user.id)
        if master is None:
            logger.warning(
                'Пользователь username={}, user_id={} не является мастером',
                user.username,
                user.id,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=NOT_A_MASTER,
            )
        if user.role != UserRole.MASTER:
            logger.warning(
                'Попытка выдать себя за мастера: username={}, user_id={}',
                user.username,
                user.id,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=NOT_A_MASTER,
            )

        if master.user_id != user.id:
            logger.warning(
                'Пользователь username={}, user_id={} не является мастером',
                user.username,
                user.id,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=NOT_A_MASTER,
            )

        return master


master_manager = MasterManager(master_crud)
