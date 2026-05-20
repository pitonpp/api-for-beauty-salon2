from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.appointment import CRUDAppointment, crud_appointment
from app.models.appointment import Appointment
from app.models.master_service import MasterService
from app.models.user import User
from app.schemas.appointment import (
    AppointmentAdminCreate,
    AppointmentAdminUpdate,
    AppointmentCreate,
    AppointmentMasterUpdate,
    AppointmentUpdate,
)
from app.schemas.status_enum import AppointmentStatus, UserRole

from .base import BaseService
from .service import service_manager
from .master_service import master_service_manager
from .master import master_manager


class AppointmentService(BaseService[Appointment, CRUDAppointment]):
    model = Appointment

    def __init__(self, crud: CRUDAppointment):
        super().__init__(crud)
        self.service_manager = service_manager
        self.master_service_manager = master_service_manager
        self.master_manager = master_manager

    async def check_time_available(
        self,
        appointment_time: datetime,
        session: AsyncSession,
        duration: timedelta,
        exclude_id: int | None = None,
    ) -> None:
        now = datetime.now().date()

        if appointment_time.date() < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя записываться на прошедшее время",
            )

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
        if user.role != UserRole.ADMIN and appointment.client_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нельзя менять/просматривать чужую запись",
            )

    async def _validate_and_get_service_and_master(
        self,
        appointment_time: datetime,
        session: AsyncSession,
        master_service_id: int,
    ) -> MasterService:
        master_service = await self.master_service_manager.get_object_or_404(
            master_service_id, session
        )
        await self.check_time_available(
            appointment_time,
            session,
            master_service.duration,
        )
        return master_service

    async def _create_appointment(
        self,
        session: AsyncSession,
        master_service_id: int,
        request_data: dict,
    ) -> Appointment:
        master_service = await self._validate_and_get_service_and_master(
            request_data["appointment_time"],
            session,
            master_service_id,
        )
        request_data["price_at_booking"] = master_service.price
        appointment = await self.crud.create(request_data, session)
        appointment.master_service = master_service
        return appointment

    async def create_appointment(
        self,
        request: AppointmentCreate,
        session: AsyncSession,
        user: User,
        master_service_id: int,
    ) -> Appointment:
        request_data = request.model_dump()
        request_data.update(
            {
                "client_id": user.id,
                "master_service_id": master_service_id,
            }
        )

        return await self._create_appointment(
            session,
            master_service_id,
            request_data,
        )

    async def admin_create_appointment(
        self,
        request: AppointmentAdminCreate,
        session: AsyncSession,
    ) -> Appointment:
        return await self._create_appointment(
            session,
            request.master_service_id,
            request.model_dump(),
        )

    async def update_appointment(
        self,
        request: AppointmentUpdate,
        session: AsyncSession,
        appointment_id: int,
        user: User,
    ) -> Appointment:
        appointment = await self.get_object_or_404(appointment_id, session)

        self._check_permissions(user, appointment)

        if request.appointment_time:
            master_service = (
                await self.master_service_manager.get_object_or_404(
                    appointment.master_service_id, session
                )
            )
            await self.check_time_available(
                request.appointment_time,
                session,
                master_service.duration,
            )

        return await self.crud.update(appointment, request, session)

    async def master_update_appointment(
        self,
        request: AppointmentMasterUpdate,
        session: AsyncSession,
        appointment_id: int,
    ) -> Appointment:
        appointment = await self.get_object_or_404(appointment_id, session)
        return await self.crud.update(appointment, request, session)

    async def admin_update_appointment(
        self,
        request: AppointmentAdminUpdate,
        session: AsyncSession,
        appointment_id: int,
    ) -> Appointment:
        appointment = await self.get_object_or_404(appointment_id, session)

        new_time = request.appointment_time or appointment.appointment_time

        if request.master_service_id:
            master_service = (
                await self.master_service_manager.get_object_or_404(
                    request.master_service_id,
                    session,
                )
            )
        else:
            master_service = appointment.master_service

        if request.appointment_time or request.master_service_id:
            await self.check_time_available(
                new_time,
                session,
                master_service.duration,
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
            session,
            user.id,
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

    async def get_master_appointments(
        self,
        session: AsyncSession,
        user: User,
    ) -> list[Appointment]:
        master = await self.master_manager.get_master_by_user_id(
            session,
            user,
        )
        return await self.crud.get_master_appointments_with_relation(
            session,
            master.id,
        )

    async def get_master_appointment(
        self,
        session: AsyncSession,
        user: User,
        appointment_id: int,
    ) -> Appointment:
        master = await self.master_manager.get_master_by_user_id(
            session,
            user,
        )
        result = await self.crud.get_master_appointment_with_relation(
            session,
            master.id,
            appointment_id,
        )
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Запись не найдена",
            )
        return result


appointment_service = AppointmentService(crud_appointment)
