"""Database model schemas and shared Pydantic/SQLModel types."""

import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import EmailStr
from sqlalchemy import Column, DateTime
from sqlalchemy.types import JSON
from sqlmodel import Field, Relationship, SQLModel

from backend.core.constants import constants


def get_datetime_utc() -> datetime:
    """Return the current UTC datetime for default timestamp fields."""
    return datetime.now(UTC)


# Shared properties
class UserBase(SQLModel):
    """Base schema shared by all user-related models."""

    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    """Schema for creating a new user with a required password."""

    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    """Schema for public user self-registration."""

    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(SQLModel):
    """Schema for updating user properties as an administrator."""

    email: EmailStr | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    is_superuser: bool | None = None
    full_name: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    """Schema for a user updating their own profile."""

    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    """Schema for updating a user's password."""

    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Many-to-many junction tables (must be defined before table models that reference them)
class RolePermission(SQLModel, table=True):  # type: ignore[call-arg]
    """Association table linking roles and permissions."""

    role_id: uuid.UUID = Field(
        foreign_key="role.id", primary_key=True, ondelete="CASCADE"
    )
    permission_id: uuid.UUID = Field(
        foreign_key="permission.id", primary_key=True, ondelete="CASCADE"
    )


class UserRole(SQLModel, table=True):  # type: ignore[call-arg]
    """Association table linking users and roles."""

    user_id: uuid.UUID = Field(
        foreign_key="user.id", primary_key=True, ondelete="CASCADE"
    )
    role_id: uuid.UUID = Field(
        foreign_key="role.id", primary_key=True, ondelete="CASCADE"
    )


# Database model, database table inferred from class name
class User(UserBase, table=True):  # type: ignore[call-arg]
    """Database model representing an application user."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str = Field(default="")
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
    # Microsoft Entra fields
    azure_user_id: str | None = Field(default=None, index=True)
    azure_tenant_id: str | None = Field(default=None)
    azure_roles: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    # Google OAuth fields
    google_id: str | None = Field(default=None, index=True)
    google_email: str | None = Field(default=None, index=True)

    # GitHub OAuth fields
    github_id: int | None = Field(default=None, index=True)
    github_username: str | None = Field(default=None, index=True)
    avatar_url: str | None = Field(default=None, max_length=500)

    files: list["File"] = Relationship(back_populates="owner", cascade_delete=True)
    tasks: list["Task"] = Relationship(back_populates="owner", cascade_delete=True)
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)
    tenant_roles: list["UserTenantRole"] = Relationship(
        back_populates="user", cascade_delete=True
    )
    roles: list["Role"] = Relationship(back_populates="users", link_model=UserRole)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    """Public API schema for user data returned to clients."""

    id: uuid.UUID
    created_at: datetime | None = None
    azure_user_id: str | None = None
    azure_tenant_id: str | None = None
    azure_roles: list[str] = []
    roles: list["RolePublic"] = Field(default_factory=list)
    google_id: str | None = None
    github_id: int | None = None
    avatar_url: str | None = None


class UsersPublic(SQLModel):
    """Response schema for paginated user lists."""

    data: list[UserPublic]
    count: int


# --- Microsoft Tenant Models ---


class MicrosoftTenantBase(SQLModel):
    """Base schema for Microsoft tenant configuration."""

    tenant_id: str = Field(unique=True, index=True, max_length=255)
    tenant_name: str = Field(max_length=255)
    is_enabled: bool = True
    auto_create_users: bool = True


class MicrosoftTenantCreate(MicrosoftTenantBase):
    """Schema for creating a Microsoft tenant."""


class MicrosoftTenantUpdate(SQLModel):
    """Schema for updating Microsoft tenant metadata."""

    tenant_name: str | None = Field(default=None, max_length=255)
    is_enabled: bool | None = None
    auto_create_users: bool | None = None


class MicrosoftTenant(MicrosoftTenantBase, table=True):  # type: ignore[call-arg]
    """Database model for a Microsoft Entra tenant."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
    created_by: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", ondelete="SET NULL"
    )
    tenant_roles: list["UserTenantRole"] = Relationship(
        back_populates="tenant", cascade_delete=True
    )


class MicrosoftTenantPublic(MicrosoftTenantBase):
    """Public API schema for a Microsoft tenant."""

    id: uuid.UUID
    created_at: datetime | None = None
    created_by: uuid.UUID | None = None


class MicrosoftTenantsPublic(SQLModel):
    """Response schema for a paginated tenant list."""

    data: list[MicrosoftTenantPublic]
    count: int


# --- RBAC Models (Roles and Permissions) ---


class PermissionBase(SQLModel):
    """Base schema for permissions used by RBAC."""

    name: str = Field(unique=True, index=True, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    resource: str = Field(max_length=255)  # e.g., "users", "reports"


class PermissionCreate(PermissionBase):
    """Schema for creating a permission."""


class PermissionUpdate(SQLModel):
    """Schema for updating an existing permission."""

    name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    resource: str | None = Field(default=None, max_length=255)


class RoleBase(SQLModel):
    """Base schema for RBAC roles."""

    name: str = Field(unique=True, index=True, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    is_system: bool = False  # True for default roles synced from config


class RoleCreate(RoleBase):
    """Schema for creating a new role."""

    permission_ids: list[uuid.UUID] = Field(default_factory=list)
    entra_role_id: str | None = Field(default=None, max_length=255)


class RoleUpdate(SQLModel):
    """Schema for updating a role."""

    name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    permission_ids: list[uuid.UUID] | None = None
    entra_role_id: str | None = Field(default=None, max_length=255)


class Permission(PermissionBase, table=True):  # type: ignore[call-arg]
    """Database model for a permission."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
    roles: list["Role"] = Relationship(
        back_populates="permissions",
        link_model=RolePermission,
    )


class PermissionPublic(PermissionBase):
    """Public response schema for permission details."""

    id: uuid.UUID
    created_at: datetime | None = None


class PermissionsPublic(SQLModel):
    """Response schema for paginated permission lists."""

    data: list[PermissionPublic]
    count: int


class Role(RoleBase, table=True):  # type: ignore[call-arg]
    """Database model for RBAC roles."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
    entra_role_id: str | None = Field(default=None, max_length=255, nullable=True)
    permissions: list[Permission] = Relationship(
        back_populates="roles",
        link_model=RolePermission,
    )
    users: list["User"] = Relationship(
        back_populates="roles",
        link_model=UserRole,
    )


class RolePublic(RoleBase):
    """Public API schema for role details."""

    id: uuid.UUID
    created_at: datetime | None = None
    entra_role_id: str | None = None
    permissions: list[PermissionPublic] = Field(default_factory=list)


class RolesPublic(SQLModel):
    """Response schema for paginated role lists."""

    data: list[RolePublic]
    count: int


class EntraAppRoleManifestEntry(SQLModel):
    """Single Microsoft Entra app role manifest entry."""

    id: str
    allowedMemberTypes: list[str] = Field(
        default_factory=lambda: [constants.entra.APP_ROLE_MEMBER_TYPE_USER]
    )
    description: str
    displayName: str
    isEnabled: bool = True
    origin: str = "Application"
    value: str


class EntraAppRoleManifestPublic(SQLModel):
    """Exportable Microsoft Entra app role manifest payload."""

    appRoles: list[EntraAppRoleManifestEntry]


# --- User-Tenant Role Mapping ---


class UserTenantRoleBase(SQLModel):
    """Base schema for user-tenant role assignments."""

    roles: list[str] = Field(default_factory=list, sa_column=Column(JSON))


class UserTenantRole(UserTenantRoleBase, table=True):  # type: ignore[call-arg]
    """Database model mapping users to roles within tenants."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    tenant_id: uuid.UUID = Field(foreign_key="microsofttenant.id", ondelete="CASCADE")
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
    user: User | None = Relationship(back_populates="tenant_roles")
    tenant: MicrosoftTenant | None = Relationship(back_populates="tenant_roles")


class UserTenantRolePublic(SQLModel):
    """Public API schema for user-tenant role mappings."""

    id: uuid.UUID
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    roles: list[str] = []
    created_at: datetime | None = None


# --- File Storage Models ---


class FileBase(SQLModel):
    """Base schema for file metadata."""

    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(max_length=127)
    size: int = Field(ge=0)  # bytes


class FilePublic(FileBase):
    """Public API schema for file metadata."""

    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime | None = None


class FilesPublic(SQLModel):
    """Response schema for paginated file lists."""

    data: list[FilePublic]
    count: int


class File(FileBase, table=True):  # type: ignore[call-arg]
    """Database model for a stored file."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    storage_key: str = Field(max_length=1024)  # path or S3 object key
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="files")


# ---------------------------------------------------------------------------
# Background Task Models
# ---------------------------------------------------------------------------

TASK_STATUS_QUEUED = "queued"
TASK_STATUS_RUNNING = "running"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_FAILED = "failed"
TASK_STATUS_CANCELLED = "cancelled"


class TaskBase(SQLModel):
    """Base schema for background task data."""

    task_type: str = Field(max_length=100)
    queue: str = Field(default="default", max_length=50)


class TaskCreate(TaskBase):
    """Schema for enqueuing a background task."""

    task_type: Literal["send_email", "export_data", "process_file"]
    queue: Literal["default", "high", "low"] = "default"
    kwargs: dict[str, Any] = Field(default_factory=dict)


class Task(TaskBase, table=True):  # type: ignore[call-arg]
    """Database model for a background task."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    rq_job_id: str | None = Field(default=None, index=True, max_length=255)
    status: str = Field(default=TASK_STATUS_QUEUED)
    kwargs: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    result: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    error: str | None = Field(default=None)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
    started_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    completed_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    owner: User | None = Relationship(back_populates="tasks")


class TaskPublic(TaskBase):
    """Public API schema for a background task."""

    id: uuid.UUID
    rq_job_id: str | None = None
    status: str
    kwargs: dict[str, Any] = {}
    result: dict[str, Any] | None = None
    error: str | None = None
    owner_id: uuid.UUID
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class TasksPublic(SQLModel):
    """Response schema for paginated background task lists."""

    data: list[TaskPublic]
    count: int


# Generic message
class Message(SQLModel):
    """Generic message response returned by endpoints."""

    message: str


# JSON payload containing access token
class Token(SQLModel):
    """Response schema for access token authentication."""

    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    """Payload data inside the JWT access token."""

    sub: str | None = None


class NewPassword(SQLModel):
    """Schema for password reset requests."""

    token: str
    new_password: str = Field(min_length=8, max_length=128)


# ---------------------------------------------------------------------------
# Notification models (ephemeral — not stored in DB, delivered via WebSocket)
# ---------------------------------------------------------------------------


class NotificationOut(SQLModel):
    """A notification message pushed to the client over WebSocket."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: Literal["info", "success", "warning", "error"] = "info"
    title: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1, max_length=1024)
    created_at: datetime = Field(default_factory=get_datetime_utc)


class NotificationCreate(SQLModel):
    """Payload for sending a notification to the authenticated user."""

    type: Literal["info", "success", "warning", "error"] = "info"
    title: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1, max_length=1024)


class NotificationSend(NotificationCreate):
    """Payload for superusers to push a notification to any user."""

    user_id: uuid.UUID


# Shared properties
class ItemBase(SQLModel):
    """Base schema for item data."""

    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    """Schema for creating an item."""


# Properties to receive on item update
class ItemUpdate(ItemBase):
    """Schema for updating an item."""

    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):  # type: ignore[call-arg]
    """Database model for an item."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    """Public API schema for an item."""

    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime | None = None


class ItemsPublic(SQLModel):
    """Response schema for paginated item lists."""

    data: list[ItemPublic]
    count: int
