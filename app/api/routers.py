from fastapi import APIRouter

from .endpoints import client_router, appointment_router, service_router

main_router = APIRouter()

main_router.include_router(client_router, prefix="/client", tags=["Clients"])
main_router.include_router(
    appointment_router, prefix="/appointment", tags=["Appointments"]
)
main_router.include_router(
    service_router, prefix="/service", tags=["Services"]
)
