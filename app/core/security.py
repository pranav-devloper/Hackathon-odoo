"""Core security helpers: password hashing (bcrypt) and OTP generation."""
import secrets
import string

import bcrypt


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt and return the hash string."""
    pwd_bytes = password.encode("utf-8")
    hashed = bcrypt.hashpw(pwd_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Constant-time check of a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


def generate_otp(length: int = 6) -> str:
    """Generate a numeric one-time code (cryptographically strong)."""
    alphabet = string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))
