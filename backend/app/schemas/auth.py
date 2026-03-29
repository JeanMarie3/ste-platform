from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SignupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(..., min_length=3, max_length=64)
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=4, max_length=256)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=1, max_length=256)


class ResetPasswordRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: str = Field(..., min_length=5, max_length=255)
    new_password: str = Field(..., min_length=4, max_length=256)


class DeleteAccountRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=1, max_length=256)
    confirmation_text: str = Field(..., min_length=3, max_length=64)


class AuthMessage(BaseModel):
    message: str


class UserPublic(BaseModel):
    id: str
    username: str
    email: str
    role: str
    created_at: datetime
    updated_at: datetime


class UserRecord(UserPublic):
    password_hash: str
    password_salt: str

