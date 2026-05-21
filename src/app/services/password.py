from fastapi import HTTPException, status
from loguru import logger
from passlib.context import CryptContext
from passlib.exc import UnknownHashError

from app.constants import ENCODING

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Хэширует пароль через bcrypt (обрезает до 72 байт)."""
    # Обрезаем пароль до 72 байт перед хешированием
    password_bytes = password.encode(ENCODING)
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    truncated_password = password_bytes.decode(ENCODING)
    return pwd_context.hash(truncated_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет пароль против хэша."""
    if not plain_password or not hashed_password:
        logger.warning("Не был дан пароль или хэш пароля")
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except UnknownHashError as e:
        logger.exception("Ошибка хэширования пароля: {}", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка с паролем: {e}",
        )
