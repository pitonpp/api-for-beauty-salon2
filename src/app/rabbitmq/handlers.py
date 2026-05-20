import asyncio

from app.rabbitmq.connection import rabbitmq_connection_manager


async def handle_reminder(msg: dict) -> None:
    """Обработчик напоминаний: имитирует отправку уведомления."""

    print(f"Получен сообщение: {msg}")
    await asyncio.sleep(1)
    print("Отправляем сообщение об оповещении")
    await rabbitmq_connection_manager.publish(
        queue_name="reminder",
        body="Hello from RabbitMQ!",
    )
