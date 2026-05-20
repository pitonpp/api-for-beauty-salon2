from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.appointment import Appointment
from app.models.master_service import MasterService
from app.schemas import AppointmentCreate, AppointmentUpdate
from app.schemas.appointment import (
    AppointmentAdminUpdate,
    AppointmentMasterUpdate,
)


class CRUDAppointment(
    CRUDBase[
        Appointment,
        AppointmentCreate,
        AppointmentUpdate | AppointmentAdminUpdate | AppointmentMasterUpdate,
    ]
):
    """CRUD для модели Appointment с подгрузкой связанных сущностей."""

    def _get_statement(
        self,
        appointment_id: int | None = None,
        multi: bool = False,
        limit: int = 10,
        skip: int = 0,
    ) -> Select:
        """Формирует запрос с загрузкой user, service, master."""

        options = [
            selectinload(self.model.user),
            selectinload(self.model.master_service).selectinload(
                MasterService.service
            ),
            selectinload(self.model.master_service).selectinload(
                MasterService.master
            ),
        ]
        if multi:
            return (
                select(self.model)
                .options(*options)
                .limit(limit)
                .offset(skip)
                .order_by(self.model.id)
            )
        return (
            select(self.model)
            .options(*options)
            .where(self.model.id == appointment_id)
        )

    def _get_statement_for_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 10,
        multi: bool = False,
        obj_id: int | None = None,
    ) -> Select:
        """Формирует запрос записей конкретного пользователя."""

        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.master_service).selectinload(
                    MasterService.service
                ),
                selectinload(self.model.master_service).selectinload(
                    MasterService.master
                ),
                selectinload(self.model.user),
            )
            .where(self.model.client_id == user_id)
        )
        if multi:
            return stmt.offset(skip).limit(limit).order_by(self.model.id)
        return stmt.where(self.model.id == obj_id)

    def _get_statement_for_master(
        self,
        master_id: int,
        skip: int = 0,
        limit: int = 10,
        multi: bool = False,
        obj_id: int | None = None,
    ) -> Select:
        """Формирует запрос записей конкретного мастера (по его услугам)."""

        master_service_ids = select(MasterService.id).where(
            MasterService.master_id == master_id,
        )
        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.master_service).selectinload(
                    MasterService.service
                ),
                selectinload(self.model.master_service).selectinload(
                    MasterService.master
                ),
                selectinload(self.model.user),
            )
            .where(self.model.master_service_id.in_(master_service_ids))
        )
        if multi:
            return stmt.limit(limit).offset(skip).order_by(self.model.id)
        return stmt.where(self.model.id == obj_id)

    async def _reload_with_relations(
        self, session: AsyncSession, obj: Appointment
    ) -> Appointment:
        """Перезагружает объект с подгруженными связанными сущностями."""

        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.master_service).selectinload(
                    MasterService.service
                ),
                selectinload(self.model.master_service).selectinload(
                    MasterService.master
                ),
                selectinload(self.model.user),
            )
            .where(self.model.id == obj.id)
        )
        result = await session.execute(stmt)
        return result.scalar_one()

    async def create(
        self,
        request: AppointmentCreate | dict,
        session: AsyncSession,
    ) -> Appointment:
        """Создаёт запись и возвращает с подгруженными связями."""
        return await self._reload_with_relations(
            session, await super().create(request, session)
        )

    async def update(
        self,
        db_obj: Appointment,
        request: AppointmentUpdate
        | AppointmentAdminUpdate
        | AppointmentMasterUpdate
        | dict,
        session: AsyncSession,
    ) -> Appointment:
        """Обновляет запись и возвращает с подгруженными связями."""
        return await self._reload_with_relations(
            session, await super().update(db_obj, request, session)
        )

    async def get_with_relations(
        self, session: AsyncSession, obj_id: int
    ) -> Appointment | None:
        """Возвращает запись с пользователем, услугой и мастером."""
        stmt = self._get_statement(appointment_id=obj_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi_with_relations(
        self, session: AsyncSession, skip: int = 0, limit: int = 10
    ) -> list[Appointment]:
        """Возвращает список записей со всеми связанными данными."""

        stmt = self._get_statement(limit=limit, skip=skip, multi=True)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_user_appointments_with_relation(
        self,
        session: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 10,
    ) -> list[Appointment]:
        """Возвращает записи пользователя со связанными данными."""

        stmt = self._get_statement_for_user(
            user_id=user_id, skip=skip, limit=limit, multi=True
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_user_appointment_with_relation(
        self,
        session: AsyncSession,
        user_id: int,
        appointment_id: int,
    ) -> Appointment | None:
        """Возвращает конкретную запись пользователя со связанными данными."""

        stmt = self._get_statement_for_user(
            user_id=user_id,
            obj_id=appointment_id,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_master_appointments_with_relation(
        self,
        session: AsyncSession,
        master_id: int,
        skip: int = 0,
        limit: int = 10,
    ) -> list[Appointment]:
        """Возвращает записи мастера со связанными данными."""

        stmt = self._get_statement_for_master(
            master_id=master_id,
            skip=skip,
            limit=limit,
            multi=True,
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_master_appointment_with_relation(
        self,
        session: AsyncSession,
        master_id: int,
        appointment_id: int,
    ) -> Appointment | None:
        """Возвращает конкретную запись мастера со связанными данными."""

        stmt = self._get_statement_for_master(
            master_id=master_id, obj_id=appointment_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_master_appointments_with_filters(
        self,
        session: AsyncSession,
        master_id: int,
        skip: int = 0,
        **filter_by,
    ) -> list[Appointment]:
        """Возвращает записи мастера с дополнительными фильтрами (например, по статусу)."""

        stmt = self._get_statement_for_master(
            master_id=master_id,
            skip=skip,
            multi=True,
        )
        if filter_by:
            stmt = stmt.filter_by(**filter_by)
        result = await session.execute(stmt)
        return result.scalars().all()


crud_appointment = CRUDAppointment(Appointment)
