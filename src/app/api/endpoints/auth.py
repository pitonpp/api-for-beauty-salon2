from fastapi import APIRouter

from app.schemas.user import UserCreate

from ..dependencies import SessionDI, UserServiceDI


router = APIRouter()


@router.post("/sign_up")
async def sign_up(
    session: SessionDI, request: UserCreate, user_service: UserServiceDI
):
    return await user_service.create_user(session, request)
