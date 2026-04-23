from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.appointment import CRUDAppointment, crud_appointment
from app.models.appointment import Appointment
from app.models.user import User
from app.schemas.appointment import (
    AppointmentAdminUpdate,
    AppointmentCreate,
    AppointmentUpdate,
)
from app.schemas.status_enum import UserRole

from .base import BaseService
from .service import service_manager


class AppointmentService(BaseService[Appointment, CRUDAppointment]):
    model = Appointment

    def __init__(self, crud: CRUDAppointment):
        super().__init__(crud)
        self.service_manager = service_manager

    async def check_time_availabile(
        self,
        appointment_time: datetime,
        session: AsyncSession,
        duration: timedelta,
    ) -> None:
        end_time = appointment_time + duration
        stmt = select(Appointment).where(
            and_(
                Appointment.appointment_time < end_time,
                Appointment.appointment_time + duration > appointment_time,
                Appointment.status == "Запланированная",
            )
        )
        result = await session.execute(stmt)
        existing = result.scalars().first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Время записи занято",
            )

    async def create_appointment(
        self,
        service_id: int,
        request: AppointmentCreate,
        session: AsyncSession,
        user: User,
    ) -> Appointment:
        service = await self.service_manager.validate_object_id(
            service_id,
            session,
        )

        await self.check_time_availabile(
            request.appointment_time,
            session,
            service.duration,
        )
        request_data = request.model_copy(
            update={"user_id": user.id, "service_id": service_id}
        )
        return await self.crud.create(request_data, session)

    async def update_appointment(
        self,
        request: AppointmentUpdate | AppointmentAdminUpdate,
        session: AsyncSession,
        appointment_id: int,
        user: User,
    ) -> Appointment:
        appointment = await self.validate_object_id(appointment_id, session)

        if user.role != UserRole.ADMIN and appointment.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нельзя менять чужую запись",
            )

        if request.appointment_time:
            await self.check_time_availabile(
                request.appointment_time,
                session,
                appointment.service.duration,
            )

        return await self.crud.update(appointment, request, session)


appointment_service = AppointmentService(crud_appointment)
