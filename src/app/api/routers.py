from fastapi import APIRouter

from .endpoints import (
    appointment_router,
    auth_router,
    service_router,
    user_router,
)

main_router = APIRouter()

main_router.include_router(
    appointment_router, prefix="/services", tags=["Appointments"]
)
main_router.include_router(
    service_router, prefix="/services", tags=["Services"]
)
main_router.include_router(
    auth_router, prefix="/auth", tags=["Authentication"]
)
main_router.include_router(user_router, prefix="/users", tags=["Users"])
