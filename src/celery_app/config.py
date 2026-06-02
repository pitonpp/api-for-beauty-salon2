from celery.schedules import crontab
from kombu import Queue

from app.core.config import get_settings

settings = get_settings()


class CeleryConfig:
    """Конфигурация Celery."""

    broker_url = settings.broker_url
    result_backend = settings.celery_backend_result
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    timezone = 'Europe/Moscow'
    enable_utc = True
    worker_send_task_events = True
    task_send_sent_event = True
    task_track_started = True
    task_acks_late = True
    worker_prefetch_multiplier = 1

    # Настройки для совместимости
    worker_mingle = False
    broker_connection_retry_on_startup = True

    task_default_retry_delay = 300
    task_max_retries = 3

    task_time_limit = 30 * 60
    task_soft_time_limit = 25 * 60

    task_routes = {
        'send_appointment_reminder': {'queue': 'email'},
        'send_appointment_notification': {'queue': 'email'},
        'send_email': {'queue': 'email'},
    }
    task_queues = [Queue('default'), Queue('email')]

    task_default_queue = 'default'

    beat_schedule = {
        'send_appointment_reminder': {
            'task': 'send_appointment_reminder',
            'schedule': crontab(hour=5, minute=00),
        },
    }
