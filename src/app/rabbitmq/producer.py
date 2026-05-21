import aio_pika
from aio_pika import ExchangeType

from app.core.config import settings
from app.rabbitmq.connection import (
    RabbitMQConnectionManager,
    rabbitmq_connection_manager,
)
from app.rabbitmq.serializer import MessageType, json_serializer


class RabbitMQProducer:
    """Поставщик сообщений RabbitMQ."""

    def __init__(
        self,
        connection_manager: RabbitMQConnectionManager,
    ) -> None:
        """Инициализирует producer с менеджером соединения."""
        self.connection_manager = connection_manager

    async def publish(
        self,
        queue_name: str,
        message: MessageType,
        exchange_name: str | None = None,
        routing_key: str | None = None,
    ) -> None:
        """Публикует сообщение в очередь/exchange RabbitMQ."""
        connection = await self.connection_manager.get_connect()

        channel = await connection.channel()
        try:
            await channel.declare_queue(
                name=queue_name,
                durable=True,
            )

            routing_key = routing_key or queue_name

            if exchange_name:
                exchange = await channel.declare_exchange(
                    exchange_name,
                    ExchangeType.DIRECT,
                    durable=True,
                )
            else:
                exchange = channel.default_exchange

            body = json_serializer.serialize(message)

            await exchange.publish(
                aio_pika.Message(
                    body=body,
                    delivery_mode=settings.rabbitmq_delivery_mode,
                ),
                routing_key=routing_key,
            )
        finally:
            await channel.close()


rabbitmq_producer = RabbitMQProducer(rabbitmq_connection_manager)
