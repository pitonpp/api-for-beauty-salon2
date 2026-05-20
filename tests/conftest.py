from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.status_enum import UserRole
from app.services.appointment import AppointmentService, appointment_service
from app.services.auth import AuthService, auth_service


@pytest.fixture
def appointment_service_() -> AppointmentService:
    return appointment_service


@pytest.fixture
def auth_service_() -> AuthService:
    return auth_service


@pytest.fixture
def session() -> AsyncSession:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def regular_user() -> User:
    user = MagicMock(spec=User)
    user.id = 1
    user.role = UserRole.USER
    user.is_active = True
    return user


@pytest.fixture
def admin_user() -> User:
    user = MagicMock(spec=User)
    user.id = 2
    user.role = UserRole.ADMIN
    user.is_active = True
    return user


@pytest.fixture
def master_user() -> User:
    user = MagicMock(spec=User)
    user.id = 3
    user.role = UserRole.MASTER
    user.is_active = True
    return user


@pytest.fixture
def request_data():
    from app.schemas.appointment import AppointmentCreate
    return AppointmentCreate(
        appointment_time=datetime.now(timezone.utc) + timedelta(hours=2)
    )
