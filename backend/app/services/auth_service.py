import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import HTTPException, status
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_for_logout,
    decode_token,
    verify_password,
)
from app.core.token_store import refresh_token_store
from app.models.user import User

logger = logging.getLogger(__name__)
_dummy_password_hash = bcrypt.hashpw(
    b"invalid-account-placeholder", bcrypt.gensalt(rounds=12)
).decode("ascii")


def _login_failed() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def authenticate(
    session: AsyncSession,
    email: str,
    password: str,
) -> tuple[User, str, str]:
    normalized_email = email.strip().casefold()
    user = await session.scalar(
        select(User)
        .options(selectinload(User.role))
        .where(User.email == normalized_email)
        .with_for_update()
    )
    if user is None:
        await asyncio.to_thread(verify_password, password, _dummy_password_hash)
        logger.warning("auth.login_failed")
        raise _login_failed()

    if not user.is_active:
        await asyncio.to_thread(verify_password, password, user.hashed_password)
        logger.warning(
            "auth.login_inactive_account",
            extra={"user_id": str(user.id)},
        )
        raise _login_failed()

    now = datetime.now(timezone.utc)
    if user.locked_until is not None and user.locked_until > now:
        await asyncio.to_thread(verify_password, password, user.hashed_password)
        logger.warning(
            "auth.login_locked_account",
            extra={"user_id": str(user.id)},
        )
        raise _login_failed()

    if user.locked_until is not None:
        user.locked_until = None
        user.failed_login_attempts = 0

    password_valid = await asyncio.to_thread(
        verify_password, password, user.hashed_password
    )
    if not password_valid:
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.locked_until = now + timedelta(minutes=15)
            logger.warning(
                "auth.account_locked",
                extra={"user_id": str(user.id)},
            )
        await session.commit()
        logger.warning(
            "auth.login_failed",
            extra={"user_id": str(user.id)},
        )
        raise _login_failed()

    user.failed_login_attempts = 0
    user.locked_until = None
    await session.commit()
    logger.info("auth.login_succeeded", extra={"user_id": str(user.id)})
    return user, create_access_token(user), create_refresh_token(user)[0]


async def rotate_refresh_token(
    session: AsyncSession,
    refresh_token: str,
) -> tuple[User, str, str]:
    try:
        claims = decode_token(refresh_token)
        if claims.get("token_type") != "refresh":
            raise InvalidTokenError("Wrong token type")
        token_id = str(uuid.UUID(claims["jti"]))
        user_id = uuid.UUID(claims["sub"])
        expires_at = int(claims["exp"])
    except (InvalidTokenError, KeyError, TypeError, ValueError):
        logger.warning("auth.refresh_failed")
        raise _login_failed() from None

    if not await refresh_token_store.consume(token_id, expires_at):
        logger.warning("auth.refresh_replay_rejected")
        raise _login_failed()

    user = await session.scalar(
        select(User)
        .options(selectinload(User.role))
        .where(User.id == user_id, User.is_active.is_(True))
    )
    if user is None:
        logger.warning("auth.refresh_inactive_or_missing_user")
        raise _login_failed()

    access_token = create_access_token(user)
    refresh_jwt, _, _ = create_refresh_token(user)
    logger.info("auth.refresh_succeeded", extra={"user_id": str(user.id)})
    return user, access_token, refresh_jwt


async def revoke_refresh_token(refresh_token: str | None) -> str | None:
    if not refresh_token:
        return None
    try:
        claims = decode_refresh_for_logout(refresh_token)
        if claims.get("token_type") != "refresh":
            return None
        token_id = str(uuid.UUID(claims["jti"]))
        user_id = str(uuid.UUID(claims["sub"]))
        expires_at = int(claims["exp"])
    except (InvalidTokenError, KeyError, TypeError, ValueError):
        logger.info("auth.logout_invalid_refresh_cookie")
        return None
    await refresh_token_store.revoke(token_id, expires_at)
    return user_id


def access_token_expiry() -> int:
    return get_settings().access_token_expire_seconds
