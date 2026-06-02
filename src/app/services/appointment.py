from datetime import datetime, timedelta

from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import (
    APPOINTMENT_NOT_FOUND,
    CANNOT_BOOK_PAST,
    CANNOT_MODIFY_CANCELED_APPOINTMENT,
    CANNOT_MODIFY_OTHERS_APPOINTMENT,
    TIME_SLOT_TAKEN,
)
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
from celery_app.tasks.send_appointment_reminder import (
    send_appointment_notification,
)

from .base import BaseService
from .master import master_manager
from .master_service import master_service_manager
from .service import service_manager


class AppointmentService(BaseService[Appointment, CRUDAppointment]):
    """Сервис для управления записями клиентов."""

    model = Appointment

    def __init__(self, crud: CRUDAppointment) -> None:
        """Инициализирует сервис с зависимостями."""
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
        """Проверяет, что время не занято (с учётом длительности услуги)."""
        now = datetime.now().date()

        if appointment_time.date() < now:
            logger.warning(
                'Попытка записи на прошедшее время: appointment_time={}',
                appointment_time,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=CANNOT_BOOK_PAST,
            )

        end_time = appointment_time + duration
        stmt = select(Appointment).where(
            Appointment.id != exclude_id,
            Appointment.appointment_time < end_time,
            Appointment.appointment_time + duration > appointment_time,
            Appointment.status == AppointmentStatus.SCHEDULED,
        )
        stmt = stmt.with_for_update()
        result = await session.execute(stmt)
        existing = result.scalars().first()

        if existing:
            logger.warning('Конфликт времени: {} занято', appointment_time)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=TIME_SLOT_TAKEN,
            )

    def _check_permissions(
        self,
        user: User,
        appointment: Appointment,
    ) -> None:
        """Проверяет права пользователя на запись (своя или админ)."""
        if user.role != UserRole.ADMIN and appointment.client_id != user.id:
            logger.warning(
                'Пользователь user_id={} role={} не имеет прав '
                'на редактирование записи appointment_id={}',
                user.id,
                user.role,
                appointment.id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=CANNOT_MODIFY_OTHERS_APPOINTMENT,
            )

    async def _validate_and_get_service_and_master(
        self,
        appointment_time: datetime,
        session: AsyncSession,
        master_service_id: int,
    ) -> MasterService:
        """Валидирует время и возвращает услугу мастера."""
        master_service = await self.master_service_manager.get_object_or_404(
            master_service_id,
            session,
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
        """Внутренний метод создания записи с проверкой и уведомлением."""
        master_service = await self._validate_and_get_service_and_master(
            request_data['appointment_time'],
            session,
            master_service_id,
        )
        request_data['price_at_booking'] = master_service.price
        appointment = await self.create(request_data, session)
        logger.info(
            'Создана запись id={} на {}',
            appointment.id,
            request_data['appointment_time'],
        )
        appointment.master_service = master_service
        send_appointment_notification.delay(appointment.id)
        return appointment

    async def create_appointment(
        self,
        request: AppointmentCreate,
        session: AsyncSession,
        user: User,
        master_service_id: int,
    ) -> Appointment:
        """Создаёт запись для текущего пользователя."""
        request_data = request.model_dump()
        request_data.update(
            {
                'client_id': user.id,
                'master_service_id': master_service_id,
            },
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
        """Создаёт запись для любого пользователя (администратором)."""
        request_data = request.model_dump()
        request_data['client_id'] = request_data.pop('user_id')
        return await self._create_appointment(
            session,
            request.master_service_id,
            request_data,
        )

    async def update_appointment(
        self,
        request: AppointmentUpdate,
        session: AsyncSession,
        appointment_id: int,
        user: User,
    ) -> Appointment:
        """Обновляет запись пользователя (только свою)."""
        appointment = await self.get_object_or_404(appointment_id, session)

        self._check_permissions(user, appointment)

        if request.appointment_time:
            master_service = (
                await self.master_service_manager.get_object_or_404(
                    appointment.master_service_id,
                    session,
                )
            )
            await self.check_time_available(
                request.appointment_time,
                session,
                master_service.duration,
            )

        if request.status:
            logger.info(
                'Статус записи id={} изменён на {}',
                appointment.id,
                request.status,
            )

        logger.info(
            'Запись id={} обновлена пользователем #{}',
            appointment.id,
            user.id,
        )
        return await self.crud.update(appointment, request, session)

    async def master_update_appointment(
        self,
        request: AppointmentMasterUpdate,
        session: AsyncSession,
        appointment_id: int,
    ) -> Appointment:
        """Обновляет статус записи мастером."""
        appointment = await self.get_object_or_404(appointment_id, session)

        if appointment.status == AppointmentStatus.CANCELED:
            logger.warning(
                'Запись id={} отменена, статус не может быть изменён',
                appointment.id,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=CANNOT_MODIFY_CANCELED_APPOINTMENT,
            )

        if request.status:
            logger.info(
                'Статус записи id={} изменён на {}',
                appointment.id,
                request.status,
            )
        logger.info('Запись id={} обновлена', appointment.id)
        return await self.crud.update(appointment, request, session)

    async def admin_update_appointment(
        self,
        request: AppointmentAdminUpdate,
        session: AsyncSession,
        appointment_id: int,
    ) -> Appointment:
        """Обновляет запись администратором (время, услуга, статус)."""
        appointment = await self.get_object_or_404(appointment_id, session)

        new_time = request.appointment_time or appointment.appointment_time

        master_service = await self.master_service_manager.get_object_or_404(
            (
                request.master_service_id
                if request.master_service_id
                else appointment.master_service_id
            ),
            session,
        )

        if request.appointment_time or request.master_service_id:
            await self.check_time_available(
                new_time,
                session,
                master_service.duration,
                exclude_id=appointment.id,
            )
        logger.info('Запись id={} обновлена', appointment.id)
        return await self.crud.update(appointment, request, session)

    async def get_appointment_with_relations(
        self,
        session: AsyncSession,
        appointment_id: int,
    ) -> Appointment:
        """Возвращает запись со всеми связанными данными или 404."""
        result = await self.crud.get_with_relations(session, appointment_id)

        if not result:
            logger.warning(
                'Запись id={} не найдена',
                appointment_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=APPOINTMENT_NOT_FOUND,
            )

        return result

    async def get_appointments_with_relations(
        self,
        session: AsyncSession,
    ) -> list[Appointment]:
        """Возвращает все записи со связанными данными."""
        return await self.crud.get_multi_with_relations(session)

    async def get_user_appointments(
        self,
        session: AsyncSession,
        user: User,
    ) -> list[Appointment]:
        """Возвращает записи текущего пользователя."""
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
        """Возвращает конкретную запись текущего пользователя или 404."""
        result = await self.crud.get_user_appointment_with_relation(
            session,
            user.id,
            appointment_id,
        )

        if not result:
            logger.warning(
                'Запись id={} не найдена',
                appointment_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=APPOINTMENT_NOT_FOUND,
            )

        return result

    async def get_master_appointments(
        self,
        session: AsyncSession,
        user: User,
    ) -> list[Appointment]:
        """Возвращает записи текущего мастера."""
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
        """Возвращает конкретную запись текущего мастера или 404."""
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
            logger.warning(
                'Запись id={} не найдена',
                appointment_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=APPOINTMENT_NOT_FOUND,
            )
        return result


appointment_service = AppointmentService(crud_appointment)
