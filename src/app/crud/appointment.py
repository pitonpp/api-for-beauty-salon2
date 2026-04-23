from typing import Optional

from sqlalchemy import select
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
    async def get_with_relations(
        self, session: AsyncSession, obj_id: int
    ) -> Optional[Appointment]:
        stmt = (
            select(self.model)
            .options(
                selectinload(Appointment.user),
                selectinload(Appointment.service),
            )
            .where(self.model.id == obj_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi_with_relations(
        self, session: AsyncSession, skip: int = 0, limit: int = 10
    ) -> list[Appointment]:
        stmt = (
            select(self.model)
            .options(
                selectinload(Appointment.user),
                selectinload(Appointment.service),
            )
            .offset(skip)
            .limit(limit)
            .order_by(self.model.id)
        )
        result = await session.execute(stmt)
        return result.scalars().all()


crud_appointment = CRUDAppointment(Appointment)
