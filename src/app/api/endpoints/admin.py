from fastapi import APIRouter

from app.api.dependencies import (
    AllowAdminDI,
    AppointmentServiceDI,
    MasterManagerDI,
    MasterServiceManagerDI,
    ServiceManagerDI,
    SessionDI,
    UserServiceDI,
    to_schema,
    to_schema_list,
)
from app.schemas.appointment import (
    AppointmentAdminCreate,
    AppointmentAdminUpdate,
    AppointmentWithRelations,
)
from app.schemas.master import MasterAdminCreate, MasterAdminUpdate, MasterDB
from app.schemas.master_service import (
    MasterServiceCreate,
    MasterServiceDB,
    MasterServiceUpdate,
)
from app.schemas.service import ServiceCreate, ServiceShort, ServiceUpdate
from app.schemas.user import UserDB, UserUpdateAdmin

router = APIRouter()


@router.get(
    "/appointments",
    response_model=list[AppointmentWithRelations],
)
async def get_appointments(
    session: SessionDI,
    _: AllowAdminDI,
    appointment_service: AppointmentServiceDI,
) -> list[AppointmentWithRelations]:
    appointments = await appointment_service.get_appointments_with_relations(
        session
    )

    return to_schema_list(appointments, AppointmentWithRelations)


@router.get(
    "/appointments/{appointment_id}",
    response_model=AppointmentWithRelations,
)
async def get_appointment(
    session: SessionDI,
    _: AllowAdminDI,
    appointment_id: int,
    appointment_service: AppointmentServiceDI,
) -> AppointmentWithRelations:
    appointment = await appointment_service.get_appointment_with_relations(
        session,
        appointment_id,
    )
    return to_schema(appointment, AppointmentWithRelations)


@router.post(
    "/appointments",
    response_model=AppointmentWithRelations,
)
async def create_appointment(
    session: SessionDI,
    request: AppointmentAdminCreate,
    _: AllowAdminDI,
    appointment_service: AppointmentServiceDI,
) -> AppointmentWithRelations:
    appointment = await appointment_service.admin_create_appointment(
        request,
        session,
    )
    return to_schema(appointment, AppointmentWithRelations)


@router.patch(
    "/appointments/{appointment_id}",
    response_model=AppointmentWithRelations,
)
async def update_appointment(
    session: SessionDI,
    appointment_id: int,
    request: AppointmentAdminUpdate,
    appointment_service: AppointmentServiceDI,
    _: AllowAdminDI,
) -> AppointmentWithRelations:
    appointment = await appointment_service.admin_update_appointment(
        request,
        session,
        appointment_id,
    )
    return to_schema(appointment, AppointmentWithRelations)


@router.post(
    "/services",
    response_model=ServiceShort,
)
async def create_service(
    session: SessionDI,
    service_manager: ServiceManagerDI,
    _: AllowAdminDI,
    request: ServiceCreate,
) -> ServiceShort:
    service = await service_manager.create_service(session, request)
    return to_schema(service, ServiceShort)


@router.patch(
    "/services/{service_id}",
    response_model=ServiceShort,
)
async def update_service(
    session: SessionDI,
    service_manager: ServiceManagerDI,
    _: AllowAdminDI,
    service_id: int,
    request: ServiceUpdate,
) -> ServiceShort:
    service = await service_manager.update_service(
        session,
        service_id,
        request,
    )
    return to_schema(service, ServiceShort)


@router.patch(
    "/users/{user_id}",
    response_model=UserDB,
)
async def update_user(
    session: SessionDI,
    request: UserUpdateAdmin,
    user_service: UserServiceDI,
    user: AllowAdminDI,
    user_id: int,
) -> UserDB:
    user = await user_service.update_user(
        user_id,
        session,
        request,
        user,
    )
    return to_schema(user, UserDB)


@router.get(
    "/users",
    response_model=list[UserDB],
)
async def get_users(
    session: SessionDI,
    _: AllowAdminDI,
    user_service: UserServiceDI,
) -> list[UserDB]:
    users = await user_service.get_users(session)
    return to_schema_list(users, UserDB)


@router.get(
    "/users/{user_id}",
    response_model=UserDB,
)
async def get_user(
    session: SessionDI,
    user_id: int,
    user_service: UserServiceDI,
    _: AllowAdminDI,
) -> UserDB:
    user = await user_service.get_object_or_404(
        user_id,
        session,
    )
    return to_schema(user, UserDB)


@router.get(
    "/masters",
    response_model=list[MasterDB],
)
async def get_masters(
    session: SessionDI,
    master_manager: MasterManagerDI,
    _: AllowAdminDI,
) -> list[MasterDB]:
    masters = await master_manager.get_masters(session)
    return to_schema_list(masters, MasterDB)


@router.get(
    "/masters/{master_id}",
    response_model=MasterDB,
)
async def get_master(
    master_id: int,
    session: SessionDI,
    master_manager: MasterManagerDI,
    _: AllowAdminDI,
) -> MasterDB:
    master = await master_manager.get_master(
        session,
        master_id,
    )
    return to_schema(master, MasterDB)


@router.patch(
    "/masters/{master_id}",
    response_model=MasterDB,
)
async def update_master(
    master_id: int,
    session: SessionDI,
    master_manager: MasterManagerDI,
    _: AllowAdminDI,
    request: MasterAdminUpdate,
) -> MasterDB:
    master = await master_manager.update_master(
        session,
        master_id,
        request,
    )
    return to_schema(master, MasterDB)


@router.post(
    "/masters",
    response_model=MasterDB,
)
async def create_master(
    session: SessionDI,
    master_manager: MasterManagerDI,
    _: AllowAdminDI,
    request: MasterAdminCreate,
) -> MasterDB:
    master = await master_manager.create_master(
        session,
        request,
    )
    return to_schema(master, MasterDB)


@router.patch(
    "/masters/{master_id}/services/{service_id}",
    response_model=MasterServiceDB,
)
async def update_master_service(
    master_id: int,
    service_id: int,
    session: SessionDI,
    user: AllowAdminDI,
    request: MasterServiceUpdate,
    master_service_manager: MasterServiceManagerDI,
) -> MasterServiceDB:
    service = await master_service_manager.update_master_service(
        session,
        service_id,
        request,
        user,
        master_id,
    )
    return to_schema(service, MasterServiceDB)


@router.post(
    "/masters/{master_id}/services",
    response_model=MasterServiceDB,
)
async def create_master_service(
    master_id: int,
    session: SessionDI,
    _: AllowAdminDI,
    request: MasterServiceCreate,
    master_service_manager: MasterServiceManagerDI,
) -> MasterServiceDB:
    service = await master_service_manager.create_master_service_admin(
        session,
        request,
        master_id,
    )
    return to_schema(service, MasterServiceDB)


@router.get(
    "/masters/{master_id}/services",
    response_model=list[MasterServiceDB],
)
async def get_master_services(
    master_id: int,
    session: SessionDI,
    _: AllowAdminDI,
    master_service_manager: MasterServiceManagerDI,
) -> list[MasterServiceDB]:
    services = await master_service_manager.get_master_services(
        session,
        master_id,
    )
    return to_schema_list(services, MasterServiceDB)


@router.get(
    "/masters/{master_id}/services/{service_id}",
    response_model=MasterServiceDB,
)
async def get_master_service(
    master_id: int,
    service_id: int,
    session: SessionDI,
    _: AllowAdminDI,
    master_service_manager: MasterServiceManagerDI,
) -> MasterServiceDB:
    service = await master_service_manager.get_master_service(
        session,
        master_id,
        service_id,
    )
    return to_schema(service, MasterServiceDB)
