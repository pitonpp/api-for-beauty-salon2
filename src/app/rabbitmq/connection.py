import aio_pika
from aio_pika.abc import (
    AbstractRobustConnection,
)

from app.core.config import settings


class RabbitMQConnectionManager:
    """Управляет подключением к RabbitMQ."""

    """Управляет подключением к RabbitMQ."""

    def __init__(self) -> None:
        self.connection: AbstractRobustConnection | None = None

    async def connect(self):
        if self.connection:
            return self

        self.connection = await aio_pika.connect_robust(
            host=settings.rabbitmq_host,
            port=settings.rabbitmq_port,
            login=settings.rabbitmq_user,
            password=settings.rabbitmq_pass,
            virtualhost=settings.rabbitmq_vhost,
            heartbeat=settings.rabbitmq_heartbeat,
            connection_attempts=settings.rabbitmq_connection_attempts,
        )

    async def get_connect(self):
        if not self.connection:
            raise RuntimeError("RabbitMQ соединение не установлено")

        return self.connection

    async def close(self) -> None:
        """Закрывает соединение с RabbitMQ."""

        if self.connection:
            await self.connection.close()
            self.connection = None


rabbitmq_connection_manager = RabbitMQConnectionManager()
