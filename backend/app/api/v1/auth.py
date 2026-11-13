import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.rate_limit import auth_rate_limiter
from app.core.security import decode_token
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.schemas.user import UserRead
from app.services.auth_service import (
    access_token_expiry,
    authenticate,
    revoke_refresh_token,
    rotate_refresh_token,
)
from app.services.user_service import _read_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])
REFRESH_COOKIE = "RefreshToken"
REFRESH_COOKIE_PATH = "/api/v1/auth"


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _set_refresh_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        max_age=settings.refresh_token_expire_seconds,
        httponly=True,
        secure=settings.app_environment.casefold() != "development",
        samesite="lax",
        path=REFRESH_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=REFRESH_COOKIE,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.app_environment.casefold() != "development",
        samesite="lax",
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    response: Response,
    form: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    email = form.username.strip().casefold()
    await auth_rate_limiter.check(
        f"login:ip:{_client_ip(request)}",
        f"login:account:{email}",
    )
    user, access_token, refresh_token = await authenticate(
        session, email, form.password
    )
    _set_refresh_cookie(response, refresh_token)
    return TokenResponse(
        access_token=access_token,
        expires_in=access_token_expiry(),
        user=_read_user(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    refresh_token = request.cookies.get(REFRESH_COOKIE)
    account_key = "invalid"
    if refresh_token:
        try:
            claims = decode_token(refresh_token)
            if claims.get("token_type") == "refresh":
                account_key = str(claims.get("sub", "invalid"))
        except (InvalidTokenError, KeyError, TypeError, ValueError):
            logger.info("auth.refresh_rate_limit_invalid_token")
    await auth_rate_limiter.check(
        f"refresh:ip:{_client_ip(request)}",
        f"refresh:account:{account_key}",
    )
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A refresh token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user, access_token, next_refresh_token = await rotate_refresh_token(
        session, refresh_token
    )
    _set_refresh_cookie(response, next_refresh_token)
    return TokenResponse(
        access_token=access_token,
        expires_in=access_token_expiry(),
        user=_read_user(user),
    )


@router.get("/me", response_model=UserRead)
async def current_user(user: User = Depends(get_current_user)) -> UserRead:
    return _read_user(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response) -> Response:
    user_id = await revoke_refresh_token(request.cookies.get(REFRESH_COOKIE))
    _clear_refresh_cookie(response)
    logger.info("auth.logout", extra={"user_id": user_id})
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
