import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage

from celery import Task
from sqlalchemy import Date, cast, select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.appointment import Appointment
from celery_app.utility.db import get_session
from celery_app.worker import celery


@celery.task(
    name='send_appointment_notification',
    queue='email',
    bind=True,
    max_retries=3,
)
def send_appointment_notification(self: Task, appointment_id: int) -> dict:
    """Отправляет уведомление о создании записи."""
    with get_session() as session:
        stmt = (
            select(Appointment)
            .where(Appointment.id == appointment_id)
            .options(selectinload(Appointment.user))
        )
        result = session.execute(stmt)
        appointment = result.scalar_one_or_none()

        if appointment is None:
            return {
                'message': f'Запись с id {appointment_id} не найдена',
                'status': 'skipped',
            }

        user_email = appointment.user.email
        send_email.delay(
            subject='Запись на приём',
            to=user_email,
            body=f'Привет, {appointment.user.first_name}! \n'
            f'Ваша запись на приём на {appointment.appointment_time} ',
        )

        return {
            'message': f'Запись на приём на {appointment.appointment_time} '
            f'отправлена на почту {user_email}',
            'status': 'success',
        }


@celery.task(
    name='send_appointment_reminder',
    queue='email',
    bind=True,
    max_retries=3,
)
def send_appointment_reminder(self: Task) -> dict:
    """Отправляет напоминания о записях на завтра."""
    results = []
    with get_session() as session:
        tommorow = datetime.now().date() + timedelta(days=1)
        stmt = (
            select(Appointment)
            .where(cast(Appointment.appointment_time, Date) == tommorow)
            .options(selectinload(Appointment.user))
            .order_by(Appointment.appointment_time)
        )
        result = session.execute(stmt)
        appointments = result.scalars().all()

        if not appointments:
            return {
                'message': f'На {tommorow} нет записей',
                'status': 'skipped',
            }

        for appointment in appointments:
            user_email = appointment.user.email
            if not user_email:
                results.append(
                    {
                        'message': (
                            f'Пользователь {appointment.user.username}'
                            ' не имеет email'
                        ),
                        'status': 'skipped',
                    },
                )
                continue
            try:
                send_email.delay(
                    subject='Запись на приём',
                    to=user_email,
                    body=f'Привет, {appointment.user.first_name}! \n'
                    f'Ваша запись на приём на {appointment.appointment_time} ',
                )
                results.append(
                    {
                        'message': (
                            f'Запись на приём на'
                            f' {appointment.appointment_time} '
                            f'отправлена на почту {user_email}'
                        ),
                        'status': 'success',
                    },
                )
            except Exception as e:
                results.append(
                    {
                        'message': (
                            f'Ошибка при отправке записи на приём'
                            f' на {appointment.appointment_time}'
                        ),
                        'status': 'failed',
                        'error': str(e),
                    },
                )

        return {
            'message': f'Обработано {len(results)} записей',
            'status': 'success',
            'results': results,
        }


@celery.task(
    name='send_email',
    queue='email',
    bind=True,
    max_retries=3,
)
def send_email(
    self: Task,
    subject: str,
    to: str,
    body: str,
) -> None:
    """Отправляет письмо на почту через SMTP."""
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = settings.smtp_from_email
    msg['To'] = to
    msg.set_content(body)

    try:
        if settings.smtp_use_ssl:
            server = smtplib.SMTP_SSL(
                settings.smtp_host,
                settings.smtp_port,
            )
        else:
            server = smtplib.SMTP(
                settings.smtp_host,
                settings.smtp_port,
            )

        if settings.smtp_use_tls:
            server.starttls()

        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)

        server.send_message(msg)
        server.quit()

    except (smtplib.SMTPException, OSError) as e:
        raise self.retry(exc=e, countdown=300)
