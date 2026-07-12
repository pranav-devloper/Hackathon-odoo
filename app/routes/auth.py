"""Auth router: all authentication endpoints."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.roles import require_role
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    MessageResponse,
    OTPVerifyRequest,
    RefreshRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserOut,
)
from app.services import auth_service


router = APIRouter(prefix="/auth", tags=["auth"])


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        role=user.role.name if user.role else "user",
        created_at=user.created_at,
    )


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user (role = 'user') and send a verification OTP."""
    user = auth_service.signup(db, data)
    return _user_out(user)


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(data: OTPVerifyRequest, db: Session = Depends(get_db)):
    """Verify an email address using the OTP sent during signup."""
    auth_service.verify_email(db, data.email, data.code)
    return MessageResponse(message="Email verified successfully")


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate and return access + refresh tokens."""
    return auth_service.login(db, data)


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    """Rotate a refresh token for a new access + refresh token pair."""
    return auth_service.refresh(db, data.refresh_token)


@router.post("/logout", response_model=MessageResponse)
def logout(
    data: RefreshRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke the given refresh token (logout current session)."""
    auth_service.logout(db, data.refresh_token)
    return MessageResponse(message="Logged out successfully")


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Send a password-reset OTP (no indication whether the email exists)."""
    auth_service.forgot_password(db, data.email)
    return MessageResponse(message="If the email exists, a reset code has been sent")


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset a password using the OTP received from /forgot-password."""
    auth_service.reset_password(db, data.email, data.code, data.new_password)
    return MessageResponse(message="Password reset successful")


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return _user_out(current_user)


@router.get("/admin/me", response_model=UserOut)
def admin_me(current_user: User = Depends(require_role("admin"))):
    """Example admin-only endpoint (requires the 'admin' role)."""
    return _user_out(current_user)
