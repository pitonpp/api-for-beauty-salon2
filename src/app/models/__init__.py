"""Импорты всех моделей для удобного доступа."""

from .appointment import Appointment
from .master import Master
from .master_service import MasterService
from .refresh_token import RefreshToken
from .service import Service
from .user import User

__all__ = [
    "Master",
    "MasterService",
    "Appointment",
    "User",
    "Service",
    "RefreshToken",
]
