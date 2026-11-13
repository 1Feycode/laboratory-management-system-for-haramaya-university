import logging
import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import decode_token
from app.db.session import get_db_session
from app.models.user import User

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication is required",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise unauthorized
    try:
        claims = decode_token(token)
        if claims.get("token_type") != "access":
            raise InvalidTokenError("Wrong token type")
        user_id = uuid.UUID(claims["sub"])
    except (InvalidTokenError, KeyError, ValueError):
        logger.info("auth.access_token_rejected")
        raise unauthorized from None

    user = await session.scalar(
        select(User)
        .options(selectinload(User.role))
        .where(User.id == user_id)
    )
    if user is None or not user.is_active:
        logger.info("auth.inactive_or_missing_user_rejected")
        raise unauthorized
    return user


def require_roles(*roles: str) -> Callable:
    async def role_guard(user: User = Depends(get_current_user)) -> User:
        if user.role.name not in roles:
            logger.warning(
                "auth.permission_denied",
                extra={"user_id": str(user.id), "required_roles": roles},
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return user

    return role_guard
