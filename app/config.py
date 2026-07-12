"""Application configuration loaded from environment / .env file."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "Hackathon Auth API"
    DATABASE_URL: str = "sqlite:///./app.db"

    # JWT
    SECRET_KEY: str = "change-me-in-production-please-use-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OTP
    OTP_EXPIRE_MINUTES: int = 10

    # Where verification / reset links point (used in console emails)
    FRONTEND_URL: str = "http://localhost:8000"

    # Email delivery via SMTP. Leave SMTP_HOST / SMTP_USER blank to use DEV
    # console-only mode (OTPs are printed to the server log). Point these at
    # any free SMTP resource, e.g.:
    #   - Mailtrap sandbox:  host=sandbox.smtp.mailtrap.io port=587 user/pass=inbox creds
    #   - Gmail app password: host=smtp.gmail.com        port=587 user=<you>@gmail.com
    # Set SMTP_USE_SSL=True for implicit-TLS ports such as 465.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_SSL: bool = False
    EMAIL_FROM: str = "AssetFlow <no-reply@assetflow.app>"


settings = Settings()
