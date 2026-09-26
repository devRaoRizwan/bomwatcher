from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, auth_rate_limit, get_auth_service
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
Auth = Annotated[AuthService, Depends(get_auth_service)]


@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(auth_rate_limit)])
def signup(data: SignupRequest, auth: Auth):
    return auth.signup(data)


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(auth_rate_limit)])
def login(data: LoginRequest, auth: Auth):
    return auth.login(data)


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser):
    return user
