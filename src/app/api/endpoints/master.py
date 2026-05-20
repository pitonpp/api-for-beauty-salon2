"""Endpoint'ы мастеров: профиль, услуги, записи (публичные и для мастера)."""

from fastapi import APIRouter

from app.api.dependencies import (
    AllowMasterAdminDI,
    MasterManagerDI,
    MasterServiceManagerDI,
    SessionDI,
    to_schema,
    to_schema_list,
    AppointmentServiceDI,
)
from app.schemas.appointment import (
    AppointmentWithRelationsMaster,
    AppointmentMasterUpdate,
)
from app.schemas.master import (
    MasterShort,
    MasterUpdate,
)
from app.schemas.master_service import (
    MasterServiceCreate,
    MasterServiceShort,
    MasterServiceUpdate,
)

router = APIRouter()


@router.get("", response_model=list[MasterShort])
async def get_masters(
    session: SessionDI,
    master_manager: MasterManagerDI,
) -> list[MasterShort]:
    masters = await master_manager.get_masters(session)
    return to_schema_list(masters, MasterShort)


@router.patch("/me", response_model=MasterShort)
async def update_me(
    session: SessionDI,
    user: AllowMasterAdminDI,
    request: MasterUpdate,
    master_manager: MasterManagerDI,
) -> MasterShort:
    master = await master_manager.update_master(session, user, request)
    return to_schema(master, MasterShort)


@router.get("/me", response_model=MasterShort)
async def get_me(
    session: SessionDI,
    user: AllowMasterAdminDI,
    master_manager: MasterManagerDI,
) -> MasterShort:
    master = await master_manager.get_master_by_user_id(session, user)
    return to_schema(master, MasterShort)


@router.get("/me/services", response_model=list[MasterServiceShort])
async def get_me_services(
    session: SessionDI,
    user: AllowMasterAdminDI,
    master_service_manager: MasterServiceManagerDI,
) -> list[MasterServiceShort]:
    services = await master_service_manager.get_my_services(
        session,
        user,
    )
    return to_schema_list(services, MasterServiceShort)


@router.patch("/me/services/{service_id}", response_model=MasterServiceShort)
async def update_my_service(
    service_id: int,
    session: SessionDI,
    user: AllowMasterAdminDI,
    request: MasterServiceUpdate,
    master_service_manager: MasterServiceManagerDI,
) -> MasterServiceShort:
    service = await master_service_manager.update_master_service(
        session,
        service_id,
        request,
        user,
    )
    return to_schema(service, MasterServiceShort)


@router.post("/me/services", response_model=MasterServiceShort)
async def create_my_service(
    session: SessionDI,
    user: AllowMasterAdminDI,
    request: MasterServiceCreate,
    master_service_manager: MasterServiceManagerDI,
) -> MasterServiceShort:
    service = await master_service_manager.create_master_service(
        session,
        request,
        user,
    )
    return to_schema(service, MasterServiceShort)


@router.get(
    "/me/appointments", response_model=list[AppointmentWithRelationsMaster]
)
async def get_my_appointments(
    session: SessionDI,
    user: AllowMasterAdminDI,
    appointment_service: AppointmentServiceDI,
) -> list[AppointmentWithRelationsMaster]:
    appointments = await appointment_service.get_master_appointments(
        session,
        user,
    )
    return to_schema_list(appointments, AppointmentWithRelationsMaster)


@router.get(
    "/me/appointments/{appointment_id}",
    response_model=AppointmentWithRelationsMaster,
)
async def get_my_appointment(
    appointment_id: int,
    session: SessionDI,
    user: AllowMasterAdminDI,
    appointment_service: AppointmentServiceDI,
) -> AppointmentWithRelationsMaster:
    appointment = await appointment_service.get_master_appointment(
        session,
        user,
        appointment_id,
    )
    return to_schema(appointment, AppointmentWithRelationsMaster)


@router.patch(
    "/me/appointments/{appointment_id}",
    response_model=AppointmentWithRelationsMaster,
)
async def update_my_appointment(
    appointment_id: int,
    session: SessionDI,
    _: AllowMasterAdminDI,
    request: AppointmentMasterUpdate,
    appointment_service: AppointmentServiceDI,
) -> AppointmentWithRelationsMaster:
    appointment = await appointment_service.master_update_appointment(
        request,
        session,
        appointment_id,
    )
    return to_schema(appointment, AppointmentWithRelationsMaster)


@router.get("/{master_id}", response_model=MasterShort)
async def get_master(
    master_id: int,
    session: SessionDI,
    master_manager: MasterManagerDI,
) -> MasterShort:
    master = await master_manager.get_master(
        session,
        master_id,
    )
    return to_schema(master, MasterShort)


@router.get("/{master_id}/services", response_model=list[MasterServiceShort])
async def get_master_services(
    master_id: int,
    session: SessionDI,
    master_service_manager: MasterServiceManagerDI,
) -> list[MasterServiceShort]:
    services = await master_service_manager.get_master_services(
        session,
        master_id,
    )
    return to_schema_list(services, MasterServiceShort)


@router.get(
    "/{master_id}/services/{service_id}", response_model=MasterServiceShort
)
async def get_master_service(
    master_id: int,
    service_id: int,
    session: SessionDI,
    master_service_manager: MasterServiceManagerDI,
) -> MasterServiceShort:
    service = await master_service_manager.get_master_service(
        session,
        master_id,
        service_id,
    )
    return to_schema(service, MasterServiceShort)
