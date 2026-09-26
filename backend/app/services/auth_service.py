from app.core import security
from app.core.exceptions import AuthenticationError, ConflictError
from app.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse


class AuthService:
    def __init__(self, users: UserRepository):
        self.users = users

    def signup(self, data: SignupRequest) -> User:
        if self.users.get_by_email(data.email):
            raise ConflictError("An account with this email already exists")
        return self.users.create(data.email, security.hash_password(data.password))

    def login(self, data: LoginRequest) -> TokenResponse:
        user = self.users.get_by_email(data.email)
        if not security.verify_password(data.password, user.password_hash if user else None) or user is None:
            raise AuthenticationError("Invalid email or password")
        token, expires_in = security.create_access_token(user.id)
        return TokenResponse(access_token=token, expires_in=expires_in)

    def user_from_token(self, token: str) -> User:
        try:
            user_id = security.decode_access_token(token)
        except security.InvalidTokenError as e:
            raise AuthenticationError(str(e)) from e
        user = self.users.get(user_id)
        if user is None:
            raise AuthenticationError("User no longer exists")
        return user
