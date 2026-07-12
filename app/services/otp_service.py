"""OTP generation/storage/verification backed by the database."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import generate_otp
from app.models.otp import OTP


def _utcnow() -> datetime:
    # Naive UTC to match how datetimes are stored in SQLite.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_otp(db: Session, user_id: int, purpose: str) -> OTP:
    """Create a fresh OTP for a user, invalidating any prior unused ones."""
    # Invalidate previous unused codes for the same purpose.
    db.execute(
        update(OTP)
        .where(OTP.user_id == user_id, OTP.purpose == purpose, OTP.used == False)  # noqa: E712
        .values(used=True)
    )

    code = generate_otp()
    expires_at = _utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    otp = OTP(user_id=user_id, code=code, purpose=purpose, expires_at=expires_at)
    db.add(otp)
    db.commit()
    db.refresh(otp)
    return otp


def verify_otp(db: Session, user_id: int, code: str, purpose: str) -> bool:
    """Return True if the most recent unused, unexpired OTP matches `code`."""
    otp = (
        db.query(OTP)
        .filter(OTP.user_id == user_id, OTP.purpose == purpose, OTP.used == False)  # noqa: E712
        .order_by(OTP.created_at.desc())
        .first()
    )
    if not otp:
        return False
    if otp.expires_at < _utcnow():
        return False
    if otp.code != code:
        return False
    otp.used = True
    db.commit()
    return True
