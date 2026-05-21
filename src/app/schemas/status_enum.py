"""Перечисления статусов записи и ролей пользователя."""

from enum import StrEnum


class AppointmentStatus(StrEnum):
    """Статус записи: запланирована, выполнена, отменена."""

    SCHEDULED = 'Запланированная'
    COMPLETED = 'Выполненная'
    CANCELED = 'Отмененная'


class UserRole(StrEnum):
    """Роль пользователя: admin, master, user."""

    ADMIN = 'admin'
    MASTER = 'master'
    USER = 'user'
