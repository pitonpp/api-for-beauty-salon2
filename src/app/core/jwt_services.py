import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from jose import ExpiredSignatureError, JWTError, jwt
from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import (
    ACTIVE_TOKEN_NOT_FOUND,
    ENCODING,
    INVALID_HASH_TOKEN,
    INVALID_TOKEN,
    INVALID_TOKEN_TYPE,
    JWT_EXP,
    JWT_JTI,
    JWT_JTI_ERROR,
    JWT_TYPE,
    JWT_TYPE_ACCESS,
    JWT_TYPE_REFRESH,
    JWT_USER_ID,
    JWT_USER_ID_ERROR,
    TOKEN_EXPIRED,
    TOKEN_NOT_FOUND,
    TOKEN_REVOKED,
)
from app.core.config import get_settings
from app.models.refresh_token import RefreshToken
from app.schemas.user import TokenData

settings = get_settings()


class InvalidTokenError(HTTPException):
    """Ошибка невалидного токена (401)."""


class ExpiredTokenError(HTTPException):
    """Ошибка истёкшего токена (401)."""


class RevokedTokenError(HTTPException):
    """Ошибка отозванного или отсутствующего токена (401/404)."""


class TokenService:
    """Сервис для создания, проверки и управления JWT-токенами."""

    def __init__(self) -> None:
        """Инициализирует сервис JWT с настройками из конфига."""
        self.secret_key = settings.secret_key
        self.refresh_secret_key = settings.refresh_secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = (
            settings.access_token_expire_minutes
        )
        self.refresh_token_expire_days = settings.refresh_token_expire_days

    def _hash_token(self, token: str) -> str:
        """Возвращает HMAC-SHA256 хэш токена."""
        return hmac.new(
            self.secret_key.encode(
                ENCODING,
            ),
            token.encode(ENCODING),
            hashlib.sha256,
        ).hexdigest()

    def _verify_token(self, token: str, stored_hash: str) -> bool:
        """Сравнивает хэш токена с сохранённым (constant-time)."""
        new_hash = self._hash_token(token)
        return hmac.compare_digest(new_hash, stored_hash)

    async def create_tokens(
        self,
        data: dict,
        session: AsyncSession,
    ) -> tuple[str, str]:
        """Создаёт и сохраняет пару access + refresh токенов."""
        access_token_data = data.copy()
        refresh_token_data = data.copy()
        now = datetime.now(timezone.utc)
        access_token_expire = now + timedelta(
            minutes=self.access_token_expire_minutes,
        )
        refresh_token_expire = now + timedelta(
            days=self.refresh_token_expire_days,
        )
        jti = uuid.uuid4()
        access_token_data.update(
            {
                JWT_EXP: access_token_expire,
                JWT_TYPE: JWT_TYPE_ACCESS,
            },
        )
        access_token = jwt.encode(
            access_token_data,
            self.secret_key,
            self.algorithm,
        )
        db_token = RefreshToken(
            user_id=refresh_token_data[JWT_USER_ID],
            expires_at=refresh_token_expire,
            jti=jti,
        )
        refresh_token_data.update(
            {
                JWT_EXP: refresh_token_expire,
                JWT_TYPE: JWT_TYPE_REFRESH,
                JWT_JTI: str(jti),
            },
        )
        refresh_token = jwt.encode(
            refresh_token_data,
            self.refresh_secret_key,
            self.algorithm,
        )
        db_token.token_hash = self._hash_token(refresh_token)

        session.add(db_token)
        await session.commit()
        logger.info(
            'Создана пара токенов для user_id={}, jti={}',
            refresh_token_data[JWT_USER_ID],
            str(jti),
        )
        return access_token, refresh_token

    def _decode_token(self, token: str, secret_key: str) -> dict[str, Any]:
        """Декодирует и проверяет JWT, выбрасывает исключения при ошибках."""
        try:
            return jwt.decode(token, secret_key, self.algorithm)
        except ExpiredSignatureError:
            logger.warning('Токен истёк')
            raise ExpiredTokenError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=TOKEN_EXPIRED,
            )
        except JWTError as e:
            logger.warning('Невалидный токен: {}', e)
            raise InvalidTokenError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=INVALID_TOKEN,
            )

    def _validate_payload(
        self,
        payload: dict[str, Any],
        token_type: str,
    ) -> TokenData:
        """Валидирует payload токена: наличие полей и соответствие типу."""
        if JWT_USER_ID not in payload:
            logger.warning('В токене отсутствует user_id')
            raise InvalidTokenError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=JWT_USER_ID_ERROR,
            )

        if JWT_TYPE not in payload or payload[JWT_TYPE] != token_type:
            logger.warning(
                'Неверный тип токена: ожидается {}, получен {}',
                token_type,
                payload.get(JWT_TYPE),
            )
            raise InvalidTokenError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=INVALID_TOKEN_TYPE,
            )

        if payload[JWT_TYPE] == JWT_TYPE_REFRESH:
            if JWT_JTI not in payload:
                logger.warning('В refresh-токене отсутствует jti')
                raise InvalidTokenError(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=JWT_JTI_ERROR,
                )

        logger.info(
            'Токен {} валиден для user_id={}',
            token_type,
            payload[JWT_USER_ID],
        )
        return TokenData(**payload)

    async def _verify_in_db(
        self,
        refresh_token: str,
        session: AsyncSession,
        jti: str,
    ) -> None:
        """Проверяет refresh-токен в БД: существование, срок, отзыв, хэш."""
        result = await session.execute(
            select(RefreshToken).where(RefreshToken.jti == uuid.UUID(jti)),
        )
        db_token = result.scalar_one_or_none()

        if db_token is None:
            logger.warning('Refresh-токен jti={} не найден в БД', jti)
            raise RevokedTokenError(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=TOKEN_NOT_FOUND,
            )

        expires_at = db_token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            logger.warning('Refresh-токен jti={} истёк', jti)
            raise ExpiredTokenError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=TOKEN_EXPIRED,
            )

        if db_token.revoked:
            logger.warning('Refresh-токен jti={} отозван', jti)
            raise RevokedTokenError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=TOKEN_REVOKED,
            )

        if not self._verify_token(refresh_token, db_token.token_hash):
            logger.warning('Хэш refresh-токена jti={} не совпадает', jti)
            raise InvalidTokenError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=INVALID_HASH_TOKEN,
            )

        logger.info('Refresh-токен jti={} успешно проверен', jti)

    def verify_access_token(
        self,
        access_token: str,
    ) -> TokenData:
        """Проверяет access-токен и возвращает его payload."""
        payload = self._decode_token(access_token, self.secret_key)
        return self._validate_payload(payload, JWT_TYPE_ACCESS)

    async def verify_refresh_token(
        self,
        refresh_token: str,
        session: AsyncSession,
    ) -> TokenData:
        """Проверяет refresh-токен (JWT + БД) и возвращает данные."""
        token_data = self._decode_token(
            refresh_token,
            self.refresh_secret_key,
        )
        token_data = self._validate_payload(token_data, JWT_TYPE_REFRESH)
        await self._verify_in_db(refresh_token, session, token_data.jti)
        return token_data

    async def revoke_all_tokens(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> None:
        """Отзывает все активные refresh-токены пользователя."""
        result = await session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked.is_(False),
            )
            .values(revoked=True),
        )
        await session.commit()
        logger.info(
            'Отозвано {} активных токенов для user_id={}',
            result.rowcount,
            user_id,
        )

    async def revoke_token(
        self,
        token_data: TokenData,
        session: AsyncSession,
    ) -> None:
        """Отзывает конкретный refresh-токен по jti."""
        result = await session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.jti == uuid.UUID(token_data.jti),
                RefreshToken.revoked.is_(False),
            )
            .values(revoked=True),
        )
        if result.rowcount == 0:
            logger.warning(
                'Активный refresh-токен jti={} не найден',
                token_data.jti,
            )
            raise RevokedTokenError(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ACTIVE_TOKEN_NOT_FOUND,
            )
        logger.info('Refresh-токен jti={} отозван', token_data.jti)
        await session.commit()

    async def refresh_tokens(
        self,
        refresh_token: str,
        session: AsyncSession,
    ) -> tuple[str, str]:
        """Обновляет пару токенов: отзывает старый refresh и создаёт новые."""
        token_data = await self.verify_refresh_token(refresh_token, session)
        await self.revoke_token(token_data, session)
        new_access_token, new_refresh_token = await self.create_tokens(
            data={JWT_USER_ID: token_data.user_id},
            session=session,
        )
        logger.info(
            'Токены обновлены для user_id={} (jti={} → новый)',
            token_data.user_id,
            token_data.jti,
        )
        return new_access_token, new_refresh_token


token_service = TokenService()
