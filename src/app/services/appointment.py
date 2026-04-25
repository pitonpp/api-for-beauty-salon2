from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.appointment import CRUDAppointment, crud_appointment
from app.models.appointment import Appointment
from app.models.service import Service
from app.models.user import User
from app.schemas.appointment import (
    AppointmentAdminCreate,
    AppointmentAdminUpdate,
    AppointmentCreate,
    AppointmentUpdate,
)
from app.schemas.status_enum import AppointmentStatus, UserRole

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
        exclude_id: int | None = None,
    ) -> None:
        end_time = appointment_time + duration
        stmt = select(Appointment).where(
            Appointment.id != exclude_id,
            Appointment.appointment_time < end_time,
            Appointment.appointment_time + duration > appointment_time,
            Appointment.status == AppointmentStatus.SCHEDULED,
        )
        result = await session.execute(stmt)
        existing = result.scalars().first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Время записи занято",
            )

    def _check_permissions(
        self, user: User, appointment: Appointment
    ) -> None:
        if user.role != UserRole.ADMIN and appointment.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нельзя менять/просматривать чужую запись",
            )

    async def _create_base(
        self,
        appointment_time: datetime,
        session: AsyncSession,
        service_id: int,
    ) -> Service:
        service = await self.service_manager.validate_object_id(
            service_id, session
        )
        await self.check_time_availabile(
            appointment_time,
            session,
            service.duration,
        )
        return service

    async def create_appointment(
        self,
        request: AppointmentCreate,
        session: AsyncSession,
        user: User,
        service_id: int,
    ) -> Appointment:
        await self._create_base(request.appointment_time, session, service_id)
        request_data = request.model_copy(
            update={"user_id": user.id, "service_id": service_id}
        )
        return await self.crud.create(request_data, session)

    async def admin_create_appointment(
        self,
        request: AppointmentAdminCreate,
        session: AsyncSession,
    ) -> Appointment:
        await self._create_base(
            request.appointment_time, session, request.service_id
        )

        return await self.crud.create(request, session)

    async def update_appointment(
        self,
        request: AppointmentUpdate,
        session: AsyncSession,
        appointment_id: int,
        user: User,
    ) -> Appointment:
        appointment = await self.validate_object_id(appointment_id, session)

        self._check_permissions(user, appointment)

        if request.appointment_time:
            service = await self.service_manager.validate_object_id(
                appointment.service_id, session
            )
            await self.check_time_availabile(
                request.appointment_time,
                session,
                service.duration,
            )

        return await self.crud.update(appointment, request, session)

    async def admin_update_appointment(
        self,
        request: AppointmentAdminUpdate,
        session: AsyncSession,
        appointment_id: int,
    ) -> Appointment:
        appointment = await self.validate_object_id(appointment_id, session)

        new_time = request.appointment_time or appointment.appointment_time

        if request.service_id:
            service = await self.service_manager.validate_object_id(
                request.service_id,
                session,
            )
        else:
            service = appointment.service

        if request.appointment_time or request.service_id:
            await self.check_time_availabile(
                new_time,
                session,
                service.duration,
                exclude_id=appointment.id,
            )

        return await self.crud.update(appointment, request, session)

    async def get_appointment_with_relations(
        self,
        session: AsyncSession,
        appointment_id: int,
    ) -> Appointment:
        result = await self.crud.get_with_relations(session, appointment_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Запись не найдена",
            )

        return result

    async def get_appointments_with_relations(
        self,
        session: AsyncSession,
    ) -> list[Appointment]:

        return await self.crud.get_multi_with_relations(session)

    async def get_user_appointments(
        self,
        session: AsyncSession,
        user: User,
    ) -> list[Appointment]:
        return await self.crud.get_user_appointments_with_relation(
            session, user.id
        )

    async def get_user_appointment(
        self,
        session: AsyncSession,
        user: User,
        appointment_id: int,
    ) -> Appointment:
        result = await self.crud.get_user_appointment_with_relation(
            session,
            user.id,
            appointment_id,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Запись не найдена",
            )

        return result


appointment_service = AppointmentService(crud_appointment)
