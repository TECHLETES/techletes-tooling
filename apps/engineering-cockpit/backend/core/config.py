"""Application configuration and environment settings."""

import warnings
from pathlib import Path
from typing import Annotated, Any, Literal, Self, cast
from urllib.parse import urlparse

from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    PostgresDsn,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.core.constants import constants

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def parse_cors(v: Any) -> list[str] | str:
    """Normalize CORS origins from a string or list value."""
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


def _frontend_origin_variants(frontend_host: str, environment: str) -> list[str]:
    parsed = urlparse(frontend_host)
    if not parsed.scheme or not parsed.netloc:
        return [frontend_host.rstrip("/")]

    origins = [frontend_host.rstrip("/")]
    hostname = parsed.hostname or ""

    if environment != "local":
        return origins

    if hostname not in {"localhost", "127.0.0.1"}:
        return origins

    local_variants = [
        "http://localhost",
        "http://localhost:5173",
        "http://localhost:5174",
        "https://localhost",
        "https://localhost:5173",
        "https://localhost:5174",
    ]
    return list(dict.fromkeys([*origins, *local_variants]))


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        # Use the repository .env for local development when present.
        # In production, settings come from the runtime environment.
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_ignore_empty=True,
        extra="ignore",
    )
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    FRONTEND_HOST: str
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = (
        []
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        """Return all allowed CORS origins, including the frontend host."""
        configured_origins = [
            str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS
        ]
        default_origins = _frontend_origin_variants(
            self.FRONTEND_HOST, self.ENVIRONMENT
        )
        return list(dict.fromkeys([*configured_origins, *default_origins]))

    PROJECT_NAME: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        """Build the SQLAlchemy database URI from environment settings."""
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: str | None = None

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48

    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        """Return True when SMTP email settings are configured."""
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    EMAIL_TEST_USER: EmailStr = "test@example.com"
    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str
    SIGNUP_ENABLED: bool = True

    # Redis
    REDIS_URL: str

    # File Storage
    # STORAGE_BACKEND: "local" stores files on disk; "s3" uses an S3-compatible service
    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    LOCAL_STORAGE_PATH: str = "/app/uploads"
    S3_BUCKET_NAME: str | None = None
    S3_ENDPOINT_URL: str | None = None  # Override for MinIO / non-AWS S3
    S3_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None

    # Microsoft Entra (Azure AD) Configuration
    AZURE_CLIENT_ID: str | None = None
    AZURE_CLIENT_SECRET: str | None = None
    AZURE_TENANT_ID: str | None = None
    AZURE_AUTHORITY: str = "https://login.microsoftonline.com"
    AZURE_GRAPH_SCOPE: str = "https://graph.microsoft.com/.default"
    AZURE_SUPERUSER_ROLE: str = (
        constants.roles.SUPER_ADMIN
    )  # Azure role name that grants superuser access

    @computed_field  # type: ignore[prop-decorator]
    @property
    def azure_enabled(self) -> bool:
        """Return True when Microsoft Entra configuration is present."""
        return bool(
            self.AZURE_CLIENT_ID and self.AZURE_CLIENT_SECRET and self.AZURE_TENANT_ID
        )

    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def google_enabled(self) -> bool:
        """Return True when Google OAuth configuration is present."""
        return bool(self.GOOGLE_CLIENT_ID and self.GOOGLE_CLIENT_SECRET)

    # GitHub OAuth Configuration
    GITHUB_CLIENT_ID: str | None = None
    GITHUB_CLIENT_SECRET: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def github_enabled(self) -> bool:
        """Return True when GitHub OAuth configuration is present."""
        return bool(self.GITHUB_CLIENT_ID and self.GITHUB_CLIENT_SECRET)

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
        )

        return self


settings = cast(Any, Settings)()
