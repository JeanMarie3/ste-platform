from fastapi import APIRouter, HTTPException

from app.schemas.auth import AuthMessage, DeleteAccountRequest, LoginRequest, ResetPasswordRequest, SignupRequest, UserPublic, ValidateSessionRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService()


@router.post("/signup", response_model=UserPublic)
def signup(payload: SignupRequest) -> UserPublic:
    try:
        return auth_service.signup(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login", response_model=UserPublic)
def login(payload: LoginRequest) -> UserPublic:
    try:
        return auth_service.login(payload)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/reset-password", response_model=AuthMessage)
def reset_password(payload: ResetPasswordRequest) -> AuthMessage:
    try:
        auth_service.reset_password(payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AuthMessage(message="Password reset successful")


@router.post("/delete-account", response_model=AuthMessage)
def delete_account(payload: DeleteAccountRequest) -> AuthMessage:
    try:
        auth_service.delete_account(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AuthMessage(message="Account deleted successfully")


@router.post("/validate-session", response_model=AuthMessage)
def validate_session(payload: ValidateSessionRequest) -> AuthMessage:
    """Return 200 if a user with matching username/email/role still exists, 404 otherwise."""
    if not auth_service.user_exists(payload.username, payload.email, payload.role):
        raise HTTPException(status_code=404, detail="User no longer exists")
    return AuthMessage(message="Session valid")

