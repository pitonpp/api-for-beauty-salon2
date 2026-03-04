from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.appointment import Appointment


class CRUDAppointment(CRUDBase):
    async def get_with_relations(
        self, session: AsyncSession, obj_id: int
    ) -> Optional[Appointment]:
        stmt = (
            select(self.model)
            .options(
                selectinload(Appointment.client),
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
                selectinload(Appointment.client),
                selectinload(Appointment.service),
            )
            .offset(skip)
            .limit(limit)
            .order_by(self.model.id)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def create_appointment(self, session: AsyncSession, request_data):
        db_obj = Appointment(**request_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj


crud_appointment = CRUDAppointment(Appointment)
