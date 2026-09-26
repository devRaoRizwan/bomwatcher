import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

_password_hash = PasswordHash.recommended()

_DUMMY_HASH = _password_hash.hash("timing-equaliser-not-a-real-password")

ACCESS_TOKEN_TYPE = "access"  # noqa: S105
GITHUB_INSTALL_STATE_TYPE = "github_install_state"


class InvalidTokenError(Exception):
    pass


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    if password_hash is None:
        _password_hash.verify(password, _DUMMY_HASH)
        return False
    return _password_hash.verify(password, password_hash)


def _encode(subject: str, token_type: str, lifetime: timedelta, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "nbf": now,
        "exp": now + lifetime,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "jti": uuid.uuid4().hex,
        **(extra or {}),
    }
    return jwt.encode(payload, settings.jwt_secret_key.get_secret_value(), algorithm=settings.jwt_algorithm)


def _decode(token: str, token_type: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={"require": ["sub", "exp", "iat", "type"]},
        )
    except jwt.ExpiredSignatureError as e:
        raise InvalidTokenError("Token has expired") from e
    except jwt.PyJWTError as e:
        raise InvalidTokenError("Invalid token") from e
    if payload.get("type") != token_type:
        raise InvalidTokenError("Invalid token type")
    return payload


def create_access_token(user_id: int) -> tuple[str, int]:
    minutes = get_settings().access_token_expire_minutes
    return _encode(str(user_id), ACCESS_TOKEN_TYPE, timedelta(minutes=minutes)), minutes * 60


def decode_access_token(token: str) -> int:
    return int(_decode(token, ACCESS_TOKEN_TYPE)["sub"])


def create_install_state(user_id: int) -> str:
    return _encode(str(user_id), GITHUB_INSTALL_STATE_TYPE, timedelta(minutes=15))


def decode_install_state(state: str) -> int:
    return int(_decode(state, GITHUB_INSTALL_STATE_TYPE)["sub"])
