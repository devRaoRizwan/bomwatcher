from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, EmailStr, Field

from app.schemas.common import Schema


def _normalise_email(v: str) -> str:
    return v.strip().lower()


Email = Annotated[EmailStr, Field(max_length=254), AfterValidator(_normalise_email)]


class SignupRequest(Schema):
    email: Email
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(Schema):
    email: Email
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(Schema):
    access_token: str
    token_type: Literal["bearer"] = "bearer"  # noqa: S105
    expires_in: int


class UserRead(Schema):
    id: int
    email: str
    created_at: datetime
