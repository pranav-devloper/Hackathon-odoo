"""JWT creation and decoding for access and refresh tokens."""
from datetime import datetime, timedelta, timezone
import uuid

import jwt

from app.config import settings


def _now() -> datetime:
    # Naive UTC to stay consistent with the rest of the codebase, which stores
    # all timestamps (OTP / refresh-token expiry, created_at, etc.) as naive UTC
    # in SQLite. Mixing tz-aware and tz-naive datetimes causes
    # "can't compare offset-naive and offset-aware datetimes" errors.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_access_token(user_id: int, role: str) -> str:
    expire = _now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    expire = _now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        # Unique id so two refresh tokens issued for the same user at the same
        # instant encode to *different* JWT strings. Without this, refresh-token
        # rotation would try to insert a token identical to the (revoked) old
        # one and hit the UNIQUE constraint on refresh_tokens.token.
        "jti": str(uuid.uuid4()),
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT. Raises jwt.InvalidTokenError on failure."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
