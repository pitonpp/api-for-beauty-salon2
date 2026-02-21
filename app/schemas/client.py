from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ClientBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=20, title="Имя")
    phone: str = Field(..., pattern=r"^\+?[1-9]\d{7,14}$")


class ClientCreate(ClientBase):
    pass


class ClientUpdate(ClientBase):
    name: Optional[str] = Field(None, min_length=2, max_length=20)
    phone: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{7,14}$")


class ClientDB(ClientBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
