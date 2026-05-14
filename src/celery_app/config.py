from kombu import Exchange, Queue

from app.core.config import settings


default_exchange = Exchange("default", type="direct")
email_exchange = Exchange("email", type="direct")
phone_exchange = Exchange("phone", type="direct")
high_priority_exchange = Exchange("high", type="direct")
broadcast_exchange = Exchange("broadcast", type="fanout")


class CeleryConfig:
    broker_url = settings.broker_url
    task_serializer = "json"
    result_serializer = "json"
    accept_content = ["json"]
    timezone = "Europe/Moscow"
    enable_utc = True
    worker_send_task_events = True
    task_send_sent_event = True

    task_time_limit = 30 * 60
    task_soft_time_limit = 25 * 60
