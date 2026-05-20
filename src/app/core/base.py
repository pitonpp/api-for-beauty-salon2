"""Импорт всех моделей для Alembic и метаданных БД."""

from app.core.db import Base  # noqa
from app.models.appointment import Appointment  # noqa
from app.models.user import User  # noqa
from app.models.service import Service  # noqa
from app.models.refresh_token import RefreshToken  # noqa
from app.models.master import Master  # noqa
from app.models.master_service import MasterService  # noqa
