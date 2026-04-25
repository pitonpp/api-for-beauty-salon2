import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Any
import uuid

from fastapi import HTTPException, status
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import (
    ENCODING,
    JWT_EXP,
    JWT_JTI,
    JWT_TYPE,
    JWT_TYPE_ACCESS,
    JWT_TYPE_REFRESH,
    JWT_USER_ID,
    JWT_JTI_ERROR,
    JWT_USER_ID_ERROR,
    TOKEN_EXPIRED,
    TOKEN_NOT_FOUND,
    TOKEN_REVOKED,
    INVALID_TOKEN,
    INVALID_TOKEN_TYPE,
    INVALID_HASH_TOKEN,
    ACTIVE_TOKEN_NOT_FOUND,
)
from app.core.config import settings
from app.models.refresh_token import RefreshToken
from app.schemas.user import TokenData


class InvalidTokenError(HTTPException):
    pass


class ExpiredTokenError(HTTPException):
    pass


class RevokedTokenError(HTTPException):
    pass


class TokenService:
    def __init__(self) -> None:
        self.secret_key = settings.secret_key
        self.refresh_secret_key = settings.refresh_secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = (
            settings.access_token_expire_minutes
        )
        self.refresh_token_expire_days = settings.refresh_token_expire_days

    def _hash_token(self, token: str) -> str:
        return hmac.new(
            self.secret_key.encode(
                ENCODING,
            ),
            token.encode(ENCODING),
            hashlib.sha256,
        ).hexdigest()

    def _verify_token(self, token: str, stored_hash: str) -> bool:
        new_hash = self._hash_token(token)
        return hmac.compare_digest(new_hash, stored_hash)

    async def create_tokens(
        self, data: dict, session: AsyncSession
    ) -> tuple[str, str]:
        access_token_data = data.copy()
        refresh_token_data = data.copy()
        now = datetime.now(timezone.utc)
        access_token_expire = now + timedelta(
            minutes=self.access_token_expire_minutes
        )
        refresh_token_expire = now + timedelta(
            days=self.refresh_token_expire_days
        )
        jti = uuid.uuid4()
        access_token_data.update(
            {
                JWT_EXP: access_token_expire,
                JWT_TYPE: JWT_TYPE_ACCESS,
            }
        )
        access_token = jwt.encode(
            access_token_data, self.secret_key, self.algorithm
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
            }
        )
        refresh_token = jwt.encode(
            refresh_token_data, self.refresh_secret_key, self.algorithm
        )
        db_token.token_hash = self._hash_token(refresh_token)

        session.add(db_token)
        await session.commit()
        return access_token, refresh_token

    def _decode_token(self, token: str, secret_key: str) -> dict[str, Any]:
        try:
            return jwt.decode(token, secret_key, self.algorithm)
        except ExpiredSignatureError:
            raise ExpiredTokenError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=TOKEN_EXPIRED,
            )
        except JWTError:
            raise InvalidTokenError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=INVALID_TOKEN,
            )

    def _validate_payload(
        self, payload: dict[str, Any], token_type: str
    ) -> TokenData:
        if JWT_USER_ID not in payload:
            raise InvalidTokenError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=JWT_USER_ID_ERROR,
            )

        if JWT_TYPE not in payload or payload[JWT_TYPE] != token_type:
            raise InvalidTokenError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=INVALID_TOKEN_TYPE,
            )

        if JWT_JTI not in payload:
            raise InvalidTokenError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=JWT_JTI_ERROR,
            )

        return TokenData(**payload)

    async def _verify_in_db(
        self, refresh_token: str, session: AsyncSession, jti: str
    ) -> None:
        result = await session.execute(
            select(RefreshToken).where(RefreshToken.jti == jti)
        )
        db_token = result.scalar_one_or_none()

        if db_token is None:
            raise RevokedTokenError(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=TOKEN_NOT_FOUND,
            )

        if db_token.expires_at < datetime.now(timezone.utc):
            raise ExpiredTokenError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=TOKEN_EXPIRED,
            )

        if db_token.revoked:
            raise RevokedTokenError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=TOKEN_REVOKED,
            )

        if not self._verify_token(refresh_token, db_token.token_hash):
            raise InvalidTokenError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=INVALID_HASH_TOKEN,
            )

    def verify_access_token(
        self,
        access_token: str,
    ):
        payload = self._decode_token(access_token, self.secret_key)
        return self._validate_payload(payload, JWT_TYPE_ACCESS)

    async def verify_refresh_token(
        self,
        refresh_token: str,
        session: AsyncSession,
    ) -> TokenData:
        token_data = self._decode_token(
            refresh_token, self.refresh_secret_key
        )
        token_data = self._validate_payload(token_data, JWT_TYPE_REFRESH)
        await self._verify_in_db(refresh_token, session, token_data.jti)
        return token_data

    async def revoke_all_tokens(
        self, session: AsyncSession, user_id: int
    ) -> None:
        result = await session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked.is_(False),
            )
            .values(revoked=True)
        )
        await session.commit()

    async def revoke_token(
        self,
        token_data: TokenData,
        session: AsyncSession,
    ) -> None:
        result = await session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.jti == token_data.jti,
                RefreshToken.revoked.is_(False),
            )
            .values(revoked=True)
        )
        if result.rowcount == 0:
            raise RevokedTokenError(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ACTIVE_TOKEN_NOT_FOUND,
            )
        await session.commit()

    async def refresh_tokens(
        self, refresh_token: str, session: AsyncSession
    ) -> tuple[str, str]:
        token_data = await self.verify_refresh_token(refresh_token, session)
        await self.revoke_token(token_data, session)
        new_access_token, new_refresh_token = await self.create_tokens(
            data={JWT_USER_ID: token_data.user_id}, session=session
        )
        return new_access_token, new_refresh_token


token_service = TokenService()
