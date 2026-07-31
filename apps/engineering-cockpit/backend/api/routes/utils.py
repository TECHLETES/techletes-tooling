"""Utility endpoints for health checks and test email functionality."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from pydantic.networks import EmailStr

from backend.api.deps import get_current_active_superuser
from backend.core.config import settings
from backend.models import Message
from backend.utils.utils import generate_test_email, send_email


class AppConfig(BaseModel):
    """Public application configuration."""

    signup_enabled: bool


router = APIRouter(prefix="/utils", tags=["utils"])


@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(email_to: EmailStr) -> Message:
    """Send a test email to the specified address."""
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email sent")


@router.get("/health-check/")
async def health_check() -> bool:
    """Return application health status."""
    return True


@router.get("/config", response_model=AppConfig)
async def get_app_config() -> AppConfig:
    """Get public application configuration."""
    return AppConfig(signup_enabled=settings.SIGNUP_ENABLED)
