import hashlib
import hmac
import os

from app.repositories.sqlite_store import AuthRepository
from app.schemas.auth import LoginRequest, ResetPasswordRequest, SignupRequest, UserPublic, UserRecord
from app.schemas.common import new_id, utc_now


class AuthService:
    def __init__(self) -> None:
        self.repository = AuthRepository()

    def signup(self, payload: SignupRequest) -> UserPublic:
        username = payload.username.strip()
        email = payload.email.strip().lower()

        if self.repository.get_by_username(username):
            raise ValueError("Username already exists")
        if self.repository.get_by_email(email):
            raise ValueError("Email already exists")

        now = utc_now()
        salt_hex = os.urandom(16).hex()
        password_hash = _hash_password(payload.password, salt_hex)
        item = UserRecord(
            id=new_id("USR"),
            username=username,
            email=email,
            role=payload.role,
            created_at=now,
            updated_at=now,
            password_hash=password_hash,
            password_salt=salt_hex,
        )
        return self.repository.create(item)

    def login(self, payload: LoginRequest) -> UserPublic:
        username = payload.username.strip()
        user = self.repository.get_by_username(username)
        if user is None:
            raise PermissionError("Invalid credentials")

        candidate_hash = _hash_password(payload.password, user.password_salt)
        if not hmac.compare_digest(candidate_hash, user.password_hash):
            raise PermissionError("Invalid credentials")

        return UserPublic(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    def reset_password(self, payload: ResetPasswordRequest) -> None:
        username = payload.username.strip()
        email = payload.email.strip().lower()
        user = self.repository.get_by_username_and_email(username, email)
        if user is None:
            raise LookupError("Username and email do not match any account")

        salt_hex = os.urandom(16).hex()
        password_hash = _hash_password(payload.new_password, salt_hex)
        self.repository.update_password(user.id, password_hash, salt_hex, utc_now())

    def list_users(self) -> list[UserPublic]:
        return self.repository.list()


def _hash_password(password: str, salt_hex: str) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 120000)
    return digest.hex()


