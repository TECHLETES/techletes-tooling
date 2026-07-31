---
name: Backend Pattern Guidelines
description: CRUD patterns, SQLModel modeling, API design, authentication, and database migrations for FastAPI backend
applyTo: backend/**/*.py, backend/tests/**/*.py
---

# Backend Development Instructions

## SQLModel & Database Patterns

### Model Structure

All database models follow this pattern: **Base → Create/Update → Public → Database**

```python
# 1. Shared properties (Base) - common to all model classes
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)

# 2. Input model (Create) - for POST requests, includes required fields
class ItemCreate(ItemBase):
    pass  # Can add fields specific to creation

# 3. Input model (Update) - for PATCH requests, all fields optional
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore

# 4. Database model (table=True) - only add here!
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
    owner_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    owner: User | None = Relationship(back_populates="items")

# 5. Output model (Public) - for GET responses, never includes secrets
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime | None = None

# 6. Response wrapper - for paginated lists
class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int
```

**Key Rules:**
- ✅ Database models use `table=True` (infers table name from class name)
- ✅ UUIDs as primary keys: `Field(default_factory=uuid.uuid4, primary_key=True)`
- ✅ Timestamps: `Field(default_factory=get_datetime_utc, sa_type=DateTime(timezone=True))`
- ✅ Foreign keys: `Field(foreign_key="table.id", ondelete="CASCADE")`
- ✅ Relationships: `Relationship(back_populates="...")`  for two-way navigation
- ❌ Never return database models directly from API (use Public models)
- ❌ Never include passwords/secrets in response models
- ❌ Never use optional PK or FK: always required

### Field Validation

Use Pydantic Field constraints:

```python
class UserCreate(UserBase):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)
    age: int | None = Field(default=None, ge=0, le=150)  # >=0, <=150
```

**Common Patterns:**
- `EmailStr` — validated email addresses
- `Field(min_length=..., max_length=...)` — string boundaries
- `Field(ge=..., le=...)` — numeric ranges (greater/less than or equal)
- `Field(unique=True, index=True)` — database constraints
- `Field(default=None)` — optional fields

### Relationships

Always use bidirectional relationships for easy navigation:

```python
# Parent
class User(UserBase, table=True):
    items: list["Item"] = Relationship(
        back_populates="owner",
        cascade_delete=True  # Delete items when user deleted
    )

# Child
class Item(ItemBase, table=True):
    owner_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        ondelete="CASCADE"  # Also handle in constraint
    )
    owner: User | None = Relationship(back_populates="items")
```

**Guidelines:**
- Use `cascade_delete=True` on Relationship to auto-delete orphans
- Use `ondelete="CASCADE"` on FK for database-level enforcement
- Use `back_populates` to create bidirectional navigation
- Child relationships are optional (`| None`), parent lists are always lists

---

## CRUD Patterns

### Create Operations

```python
def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    # Use model_validate() to convert Pydantic model to DB model
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)  # Re-fetch to get database defaults (timestamps, IDs)
    return db_item
```

**Patterns:**
- Use `model_validate()` + `update={}` to add fields not in input model
- Always `session.commit()` to persist to database
- Always `session.refresh()` after CRUD to get database-computed values
- Use keyword-only arguments (`*,`) to prevent positional arg mistakes

### Password Hashing

```python
from backend.core.security import get_password_hash, verify_password

def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create,
        update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj

def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user
```

**Security Rules:**
- Never store plain text passwords
- Use `get_password_hash()` before saving
- Use `verify_password()` to check credentials (returns `(verified: bool, updated_hash: str | None)`)
- Handle hash updates (pwdlib auto-upgrades weak hashes on verify)

### Timing Attack Prevention

When authenticating, always perform the same operations whether user exists or not:

```python
DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$..."  # Pre-computed hash

def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        # Still verify password with dummy hash to prevent timing attacks
        verify_password(password, DUMMY_HASH)
        return None
    verified, updated_password_hash = verify_password(password, db_user.hashed_password)
    if not verified:
        return None
    # Update password if cipher was upgraded
    if updated_password_hash:
        db_user.hashed_password = updated_password_hash
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
    return db_user
```

### Read Operations

```python
from sqlmodel import Session, select

def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user

def read_users(session: Session, skip: int = 0, limit: int = 100) -> UsersPublic:
    # Get total count
    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()

    # Get paginated results
    statement = select(User).order_by(col(User.created_at).desc()).offset(skip).limit(limit)
    users = session.exec(statement).all()

    return UsersPublic(data=users, count=count)
```

**Patterns:**
- Use `select()` builder for all queries
- Use `.first()` for single result, `.all()` for lists
- Use `.one()` for count/aggregate operations
- Return count with data for pagination

### Update Operations

```python
def update_item(*, session: Session, db_item: Item, item_in: ItemUpdate) -> Item:
    # Only update fields explicitly provided (exclude_unset=True)
    item_data = item_in.model_dump(exclude_unset=True)
    db_item.sqlmodel_update(item_data)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item
```

**Pattern:**
- Use `model_dump(exclude_unset=True)` to only update provided fields (not defaults)
- Use `sqlmodel_update()` to apply changes
- Always refresh after commit

### Delete Operations

```python
def delete_item(session: Session, item_id: uuid.UUID) -> None:
    db_item = session.get(Item, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    session.delete(db_item)
    session.commit()
```

---

## API Route Patterns

### Route Structure

Routes live in `backend/api/routes/` and are registered in `backend/api/main.py`.

Common route modules:

- `login.py` for login, logout, password recovery, and token test
- `users.py` for user CRUD, profile updates, and avatar upload/download
- `items.py` for item CRUD
- `rbac.py` for roles, permissions, and Entra manifest export
- `tasks.py` for task enqueueing, listing, and cancellation
- `files.py` for file upload, download, and deletion
- `admin.py` for job and queue stats
- `auth_config.py`, `auth_entra.py`, `auth_google.py`, and `auth_github.py` for auth provider config and callbacks
- `private.py` for local-only dev helpers

```python
# backend/api/routes/items.py
from fastapi import APIRouter, Depends, HTTPException
from backend.api.deps import SessionDep, CurrentUser

router = APIRouter(prefix="/items", tags=["items"])

@router.get("/", response_model=ItemsPublic)
def read_items(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Get user's items with pagination."""
    count_stmt = select(func.count()).select_from(Item).where(
        Item.owner_id == current_user.id
    )
    count = session.exec(count_stmt).one()

    stmt = (
        select(Item)
        .where(Item.owner_id == current_user.id)
        .order_by(col(Item.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    items = session.exec(stmt).all()
    return ItemsPublic(data=items, count=count)
```

### Dependency Injection Pattern

`backend/api/deps.py` centralizes all dependencies:

```python
from typing import Annotated

SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]
CurrentUser = Annotated[User, Depends(get_current_user)]

def get_current_user(session: SessionDep, token: TokenDep) -> User:
    # Validate token, fetch user from DB
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")

    user = session.get(User, token_data.sub)
    if not user or not user.is_active:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return current_user
```

**Benefits:**
- Reuse dependencies across routes
- Annotated types prevent repeated function calls
- Centralized auth logic

### Error Handling

```python
def read_item(session: SessionDep, item_id: uuid.UUID) -> ItemPublic:
    db_item = session.get(Item, item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    return db_item

@router.delete("/")
def delete_item(session: SessionDep, current_user: CurrentUser, item_id: uuid.UUID) -> Message:
    db_item = session.get(Item, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    if db_item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    session.delete(db_item)
    session.commit()
    return Message(message="Item deleted successfully")
```

**Patterns:**
- Use `HTTPException` with appropriate status codes
- Check existence before operations
- Check authorization before allowing modifications
- Return `Message` for non-GET operations with feedback

---

## Authentication & Security

### JWT Token Generation

```python
from datetime import datetime, timedelta, timezone
import jwt

ALGORITHM = "HS256"

def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

### Password Hashing

This template uses `pwdlib` with Argon2 (primary) and Bcrypt (fallback):

```python
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

password_hash = PasswordHash((Argon2Hasher(), BcryptHasher()))

def get_password_hash(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed: str) -> tuple[bool, str | None]:
    """Returns (verified, updated_hash)."""
    return password_hash.verify_and_update(plain_password, hashed)
```

**Security:**
- Argon2 is memory-hard and resistant to GPU attacks
- Bcrypt fallback for backward compatibility
- Auto-detects and upgrades weak hashes on verify

---

## Database Migrations (Alembic)

### Create a Migration

After editing `backend/models.py`:

```bash
cd backend
uv run alembic revision --autogenerate -m "add user full_name field"
```

This creates `alembic/versions/xxxx_add_user_full_name_field.py`:

```python
"""add user full_name field"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'xxxx'
down_revision: Union[str, None] = 'yyyy'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('user', sa.Column('full_name', sa.String(length=255), nullable=True))

def downgrade() -> None:
    op.drop_column('user', 'full_name')
```

### Apply Migrations

```bash
# Apply all pending migrations
uv run alembic upgrade head

# Apply specific migration
uv run alembic upgrade +1

# Rollback one migration
uv run alembic downgrade -1

# See migration history
uv run alembic history
```

### Migration Best Practices

**Guidelines:**
- ✅ Auto-generate: `uv run alembic revision --autogenerate -m "description"`
- ✅ Review generated migration before committing
- ✅ Always provide downgrade path (test with `uv run alembic downgrade -1`)
- ✅ Use descriptive names: `-m "add_item_description_field"` (lowercase, underscores)
- ✅ One logical change per migration
- ❌ Never manually edit migration versions (let alembic control them)
- ❌ Never commit uncommitted model changes when generating migrants

### Data Migrations

For data transformations (beyond schema changes):

```python
def upgrade() -> None:
    # Transform existing data
    op.execute("UPDATE users SET full_name = email WHERE full_name IS NULL")
    # Then change schema
    op.alter_column('user', 'full_name', existing_type=sa.String(), nullable=False)

def downgrade() -> None:
    op.alter_column('user', 'full_name', existing_type=sa.String(), nullable=True)
```

---

## Testing Patterns

### Test Fixtures

`tests/conftest.py` provides session and client fixtures:

```python
@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db(session)
        yield session
        # Cleanup
        statement = delete(Item)
        session.execute(statement)
        statement = delete(User)
        session.execute(statement)
        session.commit()

@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)
```

### Route Testing

```python
def test_create_item(client: TestClient, normal_user_token_headers: dict[str, str]) -> None:
    data = {"title": "Test Item", "description": "A test item"}
    response = client.post(
        "/api/v1/items/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["owner_id"]

def test_read_items(client: TestClient, normal_user_token_headers: dict[str, str]) -> None:
    response = client.get("/api/v1/items/", headers=normal_user_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert "data" in content
    assert "count" in content
```

### CRUD Testing

```python
from tests.utils.user import create_random_user

def test_create_user(db: Session) -> None:
    email = "test@example.com"
    password = "password123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)
    assert user.email == email
    assert user.id

def test_authenticate_user(db: Session) -> None:
    user = create_random_user(db)
    authenticated = crud.authenticate(session=db, email=user.email, password="password")
    assert authenticated
    assert authenticated.id == user.id
```

---

## Configuration Management

### Environment Variables

`.env` file with required variables:

```bash
# Security
SECRET_KEY=your-secret-key-here
FRONTEND_HOST=http://localhost
ENVIRONMENT=local
PROJECT_NAME=Techletes
API_V1_STR=/api/v1

# Database
POSTGRES_SERVER=db
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=app
REDIS_URL=redis://redis:6379/0

# Email (Mailcatcher for development)
SMTP_HOST=mailcatcher
SMTP_PORT=1025
EMAILS_FROM_EMAIL=admin@example.com

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:5173"]

# Initial Admin
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=initial-password
```

### Config File Pattern

`backend/core/config.py` uses Pydantic Settings:

```python
from pydantic import EmailStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = Field(..., min_length=32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    FRONTEND_HOST: str
    ENVIRONMENT: str = "local"
    PROJECT_NAME: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    REDIS_URL: str
    BACKEND_CORS_ORIGINS: list[str] = []
    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    EMAILS_FROM_EMAIL: EmailStr | None = None

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
```

---

## Common Pitfalls

| Issue | Problem | Solution |
|-------|---------|----------|
| **Returning DB model from API** | Exposes internal structure, security risk | Return Public model, use response_model |
| **Missing session.refresh()** | Relations/defaults not populated | Always refresh after create/update |
| **Direct password comparison** | Timing attacks possible | Use `verify_password()`, dummy hash |
| **Optional FK or PK** | Breaks referential integrity | Make all FKs required in model |
| **Forgetting session.commit()** | Changes not persisted | Always commit after CUD operations |
| **Not using model_validate()** | Type errors, missing fields | Use model_validate() for conversions |
| **SQL injection via f-strings** | Security vulnerability | Always use select() builder |
| **Conflicting migrations** | Alembic HEAD conflicts | Check alembic/versions/ before committing |
| **Async without async SQLModel** | Deadlocks, performance issues | Use sessionmaker(class_=AsyncSession) for async |

---

## Quick Checklist: Adding a New Model

- [ ] Create Base (shared fields)
- [ ] Create XCreate input model
- [ ] Create XUpdate input model (fields optional)
- [ ] Create X database model (table=True)
  - [ ] UUID PK with default_factory
  - [ ] created_at with get_datetime_utc
  - [ ] Any FKs with ondelete="CASCADE"
  - [ ] Relationships with back_populates
- [ ] Create XPublic output model
- [ ] Create XsPublic wrapper for lists
- [ ] Add CRUD operations in backend/crud.py or backend/crud_rbac.py
- [ ] Create API route in backend/api/routes/xs.py
- [ ] Register route in backend/api/main.py
- [ ] Generate migration: `cd backend && uv run alembic revision --autogenerate -m "..."`
- [ ] Test migration: `cd backend && uv run alembic upgrade head` then `cd backend && uv run alembic downgrade -1`
- [ ] Add tests in backend/tests/
- [ ] Frontend: `bun run generate-client`
