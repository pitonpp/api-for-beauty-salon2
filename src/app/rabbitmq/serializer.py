import json
from typing import Any

from pydantic import BaseModel

MessageType = BaseModel | dict[str, Any]


class JSONSerializer:
    """Сериализатор/десериализатор JSON для сообщений RabbitMQ."""

    @staticmethod
    def serialize(data: MessageType) -> bytes:
        """Сериализует сообщение в JSON."""
        if isinstance(data, BaseModel):
            payload = data.model_dump(mode='json')
        else:
            payload = data
        return json.dumps(payload, default=str).encode()

    @staticmethod
    def deserialize(data: bytes) -> MessageType:
        """Десериализует JSON в словарь."""
        return json.loads(data.decode())


json_serializer = JSONSerializer()
