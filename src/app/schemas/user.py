"""Pydantic-схемы для пользователей (создание, обновление, отображение)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from .custom_types import FirstAndLastName, Password, Phone, Username
from .status_enum import UserRole


class UserCreate(BaseModel):
    """Схема создания пользователя."""

    phone: Phone
    username: Username
    email: EmailStr
    first_name: FirstAndLastName
    last_name: FirstAndLastName | None = None
    password: Password

    model_config = ConfigDict(extra='forbid')


class Token(BaseModel):
    """Схема JWT-токена."""

    access_token: str
    token_type: str = 'bearer'


class TokenData(BaseModel):
    """Данные из JWT-токена."""

    user_id: int
    type: str
    jti: str | None = None


class UserShort(BaseModel):
    """Краткая схема пользователя."""

    phone: str
    email: str
    username: str
    first_name: str
    last_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserDB(UserShort):
    """Полная схема пользователя из БД."""

    id: int
    role: UserRole
    created_at: datetime
    is_active: bool


class UserUpdate(UserCreate):
    """Схема обновления пользователя."""

    first_name: FirstAndLastName | None = None
    last_name: FirstAndLastName | None = None
    password: Password | None = None
    phone: Phone | None = None
    email: EmailStr | None = None
    username: Username | None = None


class UserUpdateAdmin(UserUpdate):
    """Схема обновления пользователя администратором."""

    # role: UserRole | None = None
    is_active: bool | None = None


class UserAdminCreate(UserCreate):
    """Схема создания пользователя администратором."""

    role: UserRole = UserRole.ADMIN
