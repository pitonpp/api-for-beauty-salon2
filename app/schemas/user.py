from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.status_enum import UserRole


class UserCreate(BaseModel):
    phone: str = Field(
        ...,
        pattern=r"^\+?[7]?\d{10}$",
        description="Номер должен быть в формате +71234567890",
    )
    name: str = Field(..., min_length=2, max_length=50)
    password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="Пароль должен быть минимум 6 символов",
    )


class UserLogin(BaseModel):
    phone: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None


class UserDB(BaseModel):
    phone: str
    name: str
    role: UserRole
    created_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    password: Optional[str] = None
    phone: Optional[str] = None
    name: Optional[str] = None


class UserShort(BaseModel):
    phone: str
    name: str


class UserAdminCreate(UserCreate):
    role: UserRole = UserRole.ADMIN
