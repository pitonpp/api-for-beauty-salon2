from typing import Awaitable, Callable

from aio_pika import IncomingMessage

from app.rabbitmq.connection import (
    RabbitMQConnectionManager,
    rabbitmq_connection_manager,
)


class RabbitMQConsumer:
    """Потребитель сообщений RabbitMQ."""

    def __init__(
        self,
        connection_manager: RabbitMQConnectionManager,
    ) -> None:
        """Инициализирует consumer с менеджером соединения."""
        self.connection_manager = connection_manager

    async def start_consumer(
        self,
        queue_name: str,
        callback_func: Callable[[IncomingMessage], Awaitable[None]],
        prefetch_count: int = 1,
    ) -> None:
        """Запускает consumer для указанной очереди с заданным callback."""
        connection = await self.connection_manager.get_connect()
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=prefetch_count)
        queue = await channel.declare_queue(name=queue_name, durable=True)

        async def wrapper(message: IncomingMessage) -> None:
            async with message.process():
                await callback_func(message)

        await queue.consume(wrapper)


rabbitmq_consumer = RabbitMQConsumer(rabbitmq_connection_manager)
