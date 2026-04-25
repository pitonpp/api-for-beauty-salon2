from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.appointment import Appointment
from app.schemas import AppointmentCreate, AppointmentUpdate
from app.schemas.appointment import AppointmentAdminUpdate


class CRUDAppointment(
    CRUDBase[
        Appointment,
        AppointmentCreate,
        AppointmentUpdate | AppointmentAdminUpdate,
    ]
):
    def _get_statment(
        self,
        obj_id: int | None = None,
        multi: bool = False,
        limit: int = 10,
        skip: int = 0,
    ) -> Select:
        if multi:
            stmt = (
                select(self.model)
                .options(
                    selectinload(Appointment.user),
                    selectinload(Appointment.service),
                )
                .limit(limit)
                .offset(skip)
                .order_by(self.model.id)
            )
        else:
            stmt = (
                select(self.model)
                .options(
                    selectinload(Appointment.user),
                    selectinload(Appointment.service),
                )
                .where(self.model.id == obj_id)
            )
        return stmt

    def _get_statement_for_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 10,
        multi: bool = False,
        obj_id: int | None = None,
    ) -> Select:
        if multi:
            stmt = (
                select(self.model)
                .options(selectinload(Appointment.service))
                .where(Appointment.user_id == user_id)
                .limit(limit)
                .offset(skip)
                .order_by(self.model.id)
            )
        else:
            stmt = (
                select(self.model)
                .options(selectinload(Appointment.service))
                .where(
                    self.model.id == obj_id, Appointment.user_id == user_id
                )
            )
        return stmt

    async def get_with_relations(
        self, session: AsyncSession, obj_id: int
    ) -> Appointment | None:
        stmt = self._get_statment(obj_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi_with_relations(
        self, session: AsyncSession, skip: int = 0, limit: int = 10
    ) -> list[Appointment]:
        stmt = self._get_statment(
            limit=limit,
            skip=skip,
            multi=True,
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_user_appointments_with_relation(
        self,
        session: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 10,
    ) -> list[Appointment]:
        stmt = self._get_statement_for_user(
            user_id=user_id,
            skip=skip,
            limit=limit,
            multi=True,
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_user_appointment_with_relation(
        self, session: AsyncSession, user_id: int, appointment_id: int
    ) -> Appointment | None:
        stmt = self._get_statement_for_user(
            user_id=user_id,
            obj_id=appointment_id,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


crud_appointment = CRUDAppointment(Appointment)
