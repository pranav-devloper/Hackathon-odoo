"""Email delivery.

In this project email is sent to the *console* (DEV mode) so the API works
end-to-end without real SMTP credentials. Swap `send_email` for an SMTP
backend (e.g. FastAPI-Mail) in production.
"""
from app.config import settings


def send_email(to: str, subject: str, body: str) -> None:
    # DEV: print the "email" to stdout so codes/links are visible when testing.
    print("\n" + "=" * 64, flush=True)
    print("  [DEV EMAIL]", flush=True)
    print(f"  To:      {to}", flush=True)
    print(f"  Subject: {subject}", flush=True)
    print("-" * 64, flush=True)
    print(body, flush=True)
    print("=" * 64 + "\n", flush=True)


def send_verification_email(email: str, full_name: str, code: str) -> None:
    link = f"{settings.FRONTEND_URL}/verify?email={email}&code={code}"
    body = (
        f"Hi {full_name},\n\n"
        f"Welcome! Verify your email with this code:\n\n"
        f"    {code}\n\n"
        f"Or open this link: {link}\n\n"
        f"This code expires in {settings.OTP_EXPIRE_MINUTES} minutes."
    )
    send_email(email, "Verify your email", body)


def send_password_reset_email(email: str, full_name: str, code: str) -> None:
    body = (
        f"Hi {full_name},\n\n"
        f"Your password reset code is:\n\n"
        f"    {code}\n\n"
        f"This code expires in {settings.OTP_EXPIRE_MINUTES} minutes.\n"
        f"If you did not request this, you can ignore this email."
    )
    send_email(email, "Password reset request", body)
