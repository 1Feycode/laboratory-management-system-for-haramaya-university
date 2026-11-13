import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import get_settings

BCRYPT_ROUNDS = 12


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise ValueError("Password must not exceed 72 UTF-8 bytes")
    return bcrypt.hashpw(
        password_bytes, bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    ).decode("ascii")


def verify_password(password: str, hashed_password: str) -> bool:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        return False
    try:
        return bcrypt.checkpw(password_bytes, hashed_password.encode("ascii"))
    except (ValueError, TypeError, UnicodeEncodeError):
        return False


def _signing_key() -> str:
    return get_settings().secret_key.get_secret_value()


def create_access_token(user: Any) -> str:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(seconds=get_settings().access_token_expire_seconds)
    claims = {
        "sub": str(user.id),
        "jti": str(uuid.uuid4()),
        "email": user.email,
        "role": user.role.name,
        "dept_id": str(user.department_id) if user.department_id else None,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
        "token_type": "access",
    }
    return jwt.encode(claims, _signing_key(), algorithm="HS256")


def create_refresh_token(user: Any) -> tuple[str, str, int]:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(seconds=get_settings().refresh_token_expire_seconds)
    token_id = str(uuid.uuid4())
    claims = {
        "sub": str(user.id),
        "jti": token_id,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
        "token_type": "refresh",
    }
    return (
        jwt.encode(claims, _signing_key(), algorithm="HS256"),
        token_id,
        int(expires.timestamp()),
    )


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        _signing_key(),
        algorithms=["HS256"],
        options={"require": ["sub", "exp", "iat", "token_type"]},
    )


def decode_refresh_for_logout(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        _signing_key(),
        algorithms=["HS256"],
        options={
            "require": ["sub", "exp", "iat", "token_type"],
            "verify_exp": False,
        },
    )
