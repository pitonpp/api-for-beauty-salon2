from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .status_enum import UserRole
from .custom_types import Phone, Password, Username, FirstAndLastName


class UserCreate(BaseModel):
    phone: Phone
    username: Username
    first_name: FirstAndLastName
    last_name: FirstAndLastName | None = None
    password: Password

    model_config = ConfigDict(extra="forbid")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int | None = None
    type: str
    jti: str | None = None


class UserShort(BaseModel):
    phone: str
    username: str
    first_name: str
    last_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserDB(UserShort):
    role: UserRole
    created_at: datetime
    is_active: bool


class UserUpdate(UserCreate):
    first_name: FirstAndLastName | None = None
    last_name: FirstAndLastName | None = None
    password: Password | None = None
    phone: Phone | None = None
    username: Username | None = None


class UserUpdateAdmin(UserUpdate):
    # role: UserRole | None = None
    is_active: bool | None = None


class UserAdminCreate(UserCreate):
    role: UserRole = UserRole.ADMIN
