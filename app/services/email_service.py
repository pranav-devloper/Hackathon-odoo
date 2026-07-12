"""Email delivery.

Uses SMTP when configured (SMTP_HOST + SMTP_USER set in the environment). When
no SMTP credentials are present it falls back to printing the message to the
server console (DEV mode) so the API still works end-to-end with zero setup.

Email sends are best-effort: a failure (bad creds, network) is logged and never
breaks the calling flow (signup / forgot-password still succeed).
"""
import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

log = logging.getLogger("email")


def _smtp_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_USER)


def send_email(to: str, subject: str, body: str) -> bool:
    if not _smtp_configured():
        # DEV: print the "email" to stdout so codes/links are visible while testing.
        print("\n" + "=" * 64, flush=True)
        print("  [DEV EMAIL — SMTP not configured, printing instead]", flush=True)
        print(f"  To:      {to}", flush=True)
        print(f"  Subject: {subject}", flush=True)
        print("-" * 64, flush=True)
        print(body, flush=True)
        print("=" * 64 + "\n", flush=True)
        return False

    msg = EmailMessage()
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        if settings.SMTP_USE_SSL:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as s:
                s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                s.send_message(msg)
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as s:
                s.starttls()
                s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                s.send_message(msg)
        log.info("Email sent to %s (%s)", to, subject)
        return True
    except Exception as e:  # noqa: BLE001 — delivery must never break the flow
        log.error("Failed to send email to %s (%s): %s", to, subject, e)
        return False


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
