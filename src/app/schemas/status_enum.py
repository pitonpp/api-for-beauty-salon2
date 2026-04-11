from enum import StrEnum


class AppointmentStatus(StrEnum):
    SCHEDULED = "Запланированная"
    COMPLETED = "Выполненная"
    CANCELED = "Отмененная"


class UserRole(StrEnum):
    ADMIN = "admin"
    USER = "user"
