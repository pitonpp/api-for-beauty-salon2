"""Главный роутер, собирающий все endpoint'ы с префиксами."""

from fastapi import APIRouter

from .endpoints import (
    admin_router,
    appointment_router,
    auth_router,
    master_router,
    service_router,
    user_router,
)

main_router = APIRouter()


main_router.include_router(
    master_router,
    prefix='/masters',
    tags=['Masters'],
)

main_router.include_router(
    appointment_router,
    prefix='/appointments',
    tags=['Appointments'],
)

main_router.include_router(
    service_router,
    prefix='/services',
    tags=['Services'],
)

main_router.include_router(
    auth_router,
    prefix='/auth',
    tags=['Authentication'],
)

main_router.include_router(
    user_router,
    prefix='/users',
    tags=['Users'],
)

main_router.include_router(
    admin_router,
    prefix='/admin',
    tags=['Admin'],
)
