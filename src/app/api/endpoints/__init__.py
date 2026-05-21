"""Сбор всех роутеров endpoint'ов для подключения в routers.py."""

from .admin import router as admin_router
from .appointment import router as appointment_router
from .auth import router as auth_router
from .master import router as master_router
from .service import router as service_router
from .user import router as user_router

__all__ = [
    'admin_router',
    'appointment_router',
    'auth_router',
    'master_router',
    'service_router',
    'user_router',
]
