from kombu import Exchange, Queue

from app.core.config import get_settings

default_exchange = Exchange('default', type='direct')
email_exchange = Exchange('email', type='direct')
phone_exchange = Exchange('phone', type='direct')
high_priority_exchange = Exchange('high', type='direct')
broadcast_exchange = Exchange('broadcast', type='fanout')

settings = get_settings()


class CeleryConfig:
    """Конфигурация Celery."""

    broker_url = settings.broker_url
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
    broker_heartbeat = 0
    broker_connection_timeout = 30

    task_default_retry_delay = 300
    task_max_retries = 3

    task_time_limit = 30 * 60
    task_soft_time_limit = 25 * 60

    task_queues = (
        Queue(
            'default',
            default_exchange,
            routing_key='default',
        ),
        Queue(
            'email',
            email_exchange,
            routing_key='email',
        ),
        Queue(
            'phone',
            phone_exchange,
            routing_key='phone',
        ),
        Queue(
            'high',
            high_priority_exchange,
            routing_key='high',
        ),
        Queue(
            'broadcast',
            broadcast_exchange,
            routing_key='broadcast',
        ),
    )

    task_default_queue = 'default'
    task_default_exchange = 'default'
    task_default_routing_key = 'default'
