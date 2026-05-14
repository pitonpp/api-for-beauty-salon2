from fastapi import APIRouter

from app.schemas.appointment import AppointmentShort, AppointmentUpdate
from app.schemas.user import (
    UserCreate,
    UserDB,
    UserShort,
    UserUpdate,
    UserUpdateAdmin,
)

from ..dependencies import (
    AllowAdminDI,
    AllowUserDI,
    AppointmentServiceDI,
    SessionDI,
    UserServiceDI,
    to_schema,
    to_schema_list,
)

router = APIRouter()


@router.post("/sign_up", response_model=UserShort)
async def sign_up(
    session: SessionDI, request: UserCreate, user_service: UserServiceDI
) -> UserShort:
    user = await user_service.create_user(session, request)
    return to_schema(user, UserShort)


@router.get("/me", response_model=UserDB)
async def get_me(
    session: SessionDI,
    user: AllowUserDI,
) -> UserDB:
    return to_schema(user, UserDB)


@router.patch("/me", response_model=UserDB)
async def update_me(
    session: SessionDI,
    user: AllowUserDI,
    request: UserUpdate,
    user_service: UserServiceDI,
) -> UserDB:
    user = await user_service.update_user(user.id, session, request)
    return to_schema(user, UserDB)


@router.get(
    "/me/appointments",
    response_model=list[AppointmentShort],
)
async def get_appointments(
    session: SessionDI,
    appointment_service: AppointmentServiceDI,
    user: AllowUserDI,
) -> list[AppointmentShort]:
    appointments = await appointment_service.get_user_appointments(
        session, user
    )
    return to_schema_list(appointments, AppointmentShort)


@router.get(
    "/me/appointments/{appointment_id}",
    response_model=AppointmentShort,
)
async def get_appointment(
    session: SessionDI,
    appointment_service: AppointmentServiceDI,
    user: AllowUserDI,
    appointment_id: int,
) -> AppointmentShort:
    appointment = await appointment_service.get_user_appointment(
        session,
        user,
        appointment_id,
    )
    return to_schema(appointment, AppointmentShort)


@router.patch(
    "/me/appointments/{appointment_id}",
    response_model=AppointmentShort,
)
async def update_appointment(
    session: SessionDI,
    appointment_id: int,
    appointment_service: AppointmentServiceDI,
    request: AppointmentUpdate,
    user: AllowUserDI,
) -> AppointmentShort:
    appointment = await appointment_service.update_appointment(
        request,
        session,
        appointment_id,
        user,
    )
    return to_schema(appointment, AppointmentShort)
