"""Authentication business logic.

Groups all the auth flows so routes stay thin:
signup, verify-email, login, refresh, logout, forgot-password, reset-password.
"""
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import hash_password, verify_password
from app.models.otp import OTP
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin
from app.services.email_service import send_password_reset_email, send_verification_email
from app.services.jwt_service import create_access_token, create_refresh_token, decode_token
from app.services.otp_service import create_otp, verify_otp
from app.services import activity_service


# ---------- helpers ----------
def _utcnow() -> datetime:
    # Naive UTC to match datetimes stored in SQLite.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_role(db: Session, name: str) -> Role | None:
    return db.query(Role).filter(Role.name == name).first()


def _issue_tokens(db: Session, user: User) -> dict:
    """Create an access + refresh token pair and persist the refresh token."""
    role = user.role.name if user.role else "user"
    access = create_access_token(user.id, role)
    refresh = create_refresh_token(user.id)
    db.add(
        RefreshToken(
            user_id=user.id,
            token=refresh,
            expires_at=_utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )
    db.commit()
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


# ---------- signup ----------
def signup(db: Session, data: UserCreate) -> User:
    if get_user_by_email(db, data.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Email already registered")

    user_role = get_role(db, "user")
    if not user_role:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Default 'user' role is missing; seed roles first")

    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        role_id=user_role.id,
        is_verified=False,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    otp = create_otp(db, user.id, "email_verification")
    send_verification_email(user.email, user.full_name, otp.code)
    activity_service.log_activity(db, user.id, "user_signup", "user", user.id, user.email)
    return user


# ---------- email verification ----------
def verify_email(db: Session, email: str, code: str) -> User:
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.is_verified:
        return user
    if not verify_otp(db, user.id, code, "email_verification"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid or expired verification code")
    user.is_verified = True
    db.commit()
    db.refresh(user)
    return user


# ---------- login ----------
def authenticate(db: Session, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
    return user


def login(db: Session, data: UserLogin) -> dict:
    user = authenticate(db, data.email, data.password)
    return _issue_tokens(db, user)


# ---------- refresh ----------
def refresh(db: Session, refresh_token: str) -> dict:
    try:
        payload = decode_token(refresh_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid refresh token")
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token type")

    stored = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    if not stored or stored.revoked or stored.expires_at < _utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Refresh token revoked or expired")

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="User not found or inactive")

    # Rotate the refresh token: revoke the old one, issue a new pair.
    stored.revoked = True
    db.commit()
    return _issue_tokens(db, user)


# ---------- logout ----------
def logout(db: Session, refresh_token: str) -> None:
    stored = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    if stored and not stored.revoked:
        stored.revoked = True
        db.commit()


# ---------- forgot / reset password ----------
def forgot_password(db: Session, email: str) -> None:
    user = get_user_by_email(db, email)
    # Always return the same message so we don't leak which emails exist.
    if not user:
        return
    otp = create_otp(db, user.id, "password_reset")
    send_password_reset_email(user.email, user.full_name, otp.code)


def reset_password(db: Session, email: str, code: str, new_password: str) -> None:
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not verify_otp(db, user.id, code, "password_reset"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid or expired reset code")
    user.hashed_password = hash_password(new_password)
    db.commit()
