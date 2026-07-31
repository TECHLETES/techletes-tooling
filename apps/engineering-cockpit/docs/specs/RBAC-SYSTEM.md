# RBAC System Documentation

## Overview

This template implements a complete **Role-Based Access Control (RBAC)** system that works across both backend (FastAPI) and frontend (React). The system allows fine-grained permission management through a three-level hierarchy:

1. **Permissions** — Granular actions (e.g., `items:read`, `items:delete`)
2. **Roles** — Collections of permissions (e.g., `editor`, `viewer`, `admin`)
3. **Users** — Assigned one or more roles, inheriting all their permissions

---

## Backend RBAC Implementation

### Core Models

The RBAC system is built on three main database tables and their relationships:

#### 1. Permission Model
```python
class Permission(SQLModel, table=True):
    id: UUID
    name: str  # e.g., "items:read", "items:delete", "users:manage"
    description: str | None
    resource: str  # e.g., "items", "users", "reports"
    created_at: datetime
    roles: list[Role]  # Many-to-many relationship
```

**Key Points:**
- Permissions are **immutable** (discovered from code, not typically created via API)
- Permission names follow the format `resource:action` (e.g., `items:read`)
- Permissions are auto-discovered from backend and frontend code that uses them

#### 2. Role Model
```python
class Role(SQLModel, table=True):
    id: UUID
    name: str  # e.g., "super_admin", "editor", "viewer"
    description: str | None
    is_system: bool  # True for built-in roles (super_admin, user, etc.)
    entra_role_id: str | None  # Microsoft Entra synced role ID
    created_at: datetime
    permissions: list[Permission]  # Many-to-many relationship
    users: list[User]  # Many-to-many relationship
```

**Key Points:**
- System roles (`super_admin`, `user`) are synced from config and immutable
- Custom roles can be created via API
- Roles can be mapped to Microsoft Entra roles for SSO integration

#### 3. User-Role Association
```python
class UserRole(SQLModel, table=True):
    """Junction table linking users to roles."""
    user_id: UUID
    role_id: UUID
```

Users gain all permissions of any role they are assigned to.

### Permission Discovery System

The backend includes an **automatic permission discovery** system that scans code for permission usage patterns:

```python
from backend.core.rbac import discover_permissions

# Discovers all permissions from backend and frontend code
permissions = discover_permissions()
# Returns: {
#   "items": [{"name": "items:read", "display": "Read Items", "resource": "items"}, ...],
#   "users": [...],
#   ...
# }
```

**Discovered Patterns:**
- Backend: `require_permission("permission:name")`, `permission_dep("name")`, `require_all_permissions(...)`
- Frontend: `can("permission:name")`, `requiredPermissions: [...]`

This ensures permissions stay in sync across backend and frontend.

### System Roles & Permissions

The system includes built-in roles synchronized from config:

#### super_admin
- **Permissions:** All permissions automatically (bypasses checks)
- **User Field:** `is_superuser: bool = True`
- **Use Case:** Application administrators with unrestricted access
- **Backend Check:** `if user.is_superuser: return True`

#### user
- **Permissions:** Basic user permissions (e.g., read own items)
- **Default for:** All registered users
- **Customizable:** Add more permissions as needed

#### Custom Roles
Created via API for granular permission delegation.

### Backend Authorization

#### 1. Dependency-Based Authorization

Use FastAPI dependencies to protect routes:

```python
from backend.api.deps_rbac import require_permission, require_role

@router.delete("/items/{item_id}")
def delete_item(
    item_id: UUID,
    session: SessionDep,
    user: Annotated[User, Depends(require_permission("items:delete"))],
):
    """Only users with items:delete permission can call this."""
    item = session.get(Item, item_id)
    session.delete(item)
    session.commit()
    return {"deleted": item_id}
```

**Available Dependencies:**

```python
# Require a single role
@Depends(require_role("editor"))

# Require a single permission
@Depends(require_permission("items:delete"))

# Require ANY of these roles
@Depends(require_any_role("admin", "editor"))

# Require ALL of these permissions
@Depends(require_all_permissions("items:read", "items:update"))
```

#### 2. Manual Authorization Checks

For conditional logic within route handlers:

```python
from backend.crud_rbac import user_has_permission, user_has_role

def update_item(item_id: UUID, user: User, session: Session):
    if not user_has_permission(session, user, "items:update"):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Proceed with update
```

#### 3. Superuser Bypass

All permission checks automatically pass for users with `is_superuser=True`:

```python
def check_access(user: User, session: Session, permission: str) -> bool:
    if user.is_superuser:
        return True  # Superusers bypass all checks
    return user_has_permission(session, user, permission)
```

### RBAC API Endpoints

All endpoints require authentication (valid JWT token).

#### Permission Management (`/api/v1/rbac/permissions`)

```http
GET /api/v1/rbac/permissions
  - List all permissions
  - Query: ?skip=0&limit=100
  - Response: { data: [PermissionPublic], count: int }

GET /api/v1/rbac/permissions/{permission_id}
  - Get permission details

POST /api/v1/rbac/permissions
  - Create permission (requires "rbac:create_permissions")
  - Body: { name, description, resource }

PUT /api/v1/rbac/permissions/{permission_id}
  - Update permission (requires "rbac:update_permissions")

DELETE /api/v1/rbac/permissions/{permission_id}
  - Delete permission (requires "rbac:delete_permissions")
```

#### Role Management (`/api/v1/rbac/roles`)

```http
GET /api/v1/rbac/roles
  - List all roles
  - Response: { data: [RolePublic], count: int }

GET /api/v1/rbac/roles/{role_id}
  - Get role with permissions

POST /api/v1/rbac/roles
  - Create role (requires "rbac:manage_roles")
  - Body: { name, description, permission_ids: [UUID] }

PUT /api/v1/rbac/roles/{role_id}
  - Update role (requires "rbac:manage_roles")

DELETE /api/v1/rbac/roles/{role_id}
  - Delete role (requires "rbac:manage_roles")
  - Cannot delete system roles

GET /api/v1/rbac/roles/entra-manifest
  - Export roles as Microsoft Entra app role manifest
  - For SSO integration

POST /api/v1/rbac/roles/{role_id}/permissions/{permission_id}
  - Add permission to role (requires "rbac:manage_roles")

DELETE /api/v1/rbac/roles/{role_id}/permissions/{permission_id}
  - Remove permission from role
```

#### User Roles (`/api/v1/rbac/users/{user_id}`)

```http
GET /api/v1/rbac/users/{user_id}/roles
  - Get all roles assigned to user

POST /api/v1/rbac/users/{user_id}/roles/{role_id}
  - Assign role to user (requires "rbac:manage_roles")

DELETE /api/v1/rbac/users/{user_id}/roles/{role_id}
  - Remove role from user (requires "rbac:manage_roles")

GET /api/v1/rbac/users/{user_id}/permissions
  - Get all effective permissions (computed from roles)
```

### Database Schema

```sql
-- Permissions table
CREATE TABLE permission (
    id UUID PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description VARCHAR(500),
    resource VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE
);

-- Roles table
CREATE TABLE role (
    id UUID PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description VARCHAR(500),
    is_system BOOLEAN DEFAULT false,
    entra_role_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE
);

-- Junction table: roles ↔ permissions
CREATE TABLE rolepermission (
    role_id UUID PRIMARY KEY,
    permission_id UUID PRIMARY KEY,
    FOREIGN KEY (role_id) REFERENCES role(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permission(id) ON DELETE CASCADE
);

-- Junction table: users ↔ roles
CREATE TABLE userrole (
    user_id UUID PRIMARY KEY,
    role_id UUID PRIMARY KEY,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES role(id) ON DELETE CASCADE
);
```

---

## Frontend RBAC Usage

### Core Hooks

#### useAuth()
Primary hook for authentication and authorization. Returns current user, roles, and permission utilities.

```tsx
import useAuth from "@/hooks/useAuth"

function MyComponent() {
  const {
    user,              // Current user or null
    roles,             // Array of RolePublic
    permissions,       // Array of PermissionPublic
    hasRole,           // (name: string) => boolean
    hasPermission,     // (name: string) => boolean
    hasAnyRole,        // (...names: string[]) => boolean
    hasAllPermissions, // (...names: string[]) => boolean
    isSuperAdmin,      // () => boolean
    canAccess,         // Alias for hasPermission
  } = useAuth()

  // Check permission
  if (!user) return <p>Not logged in</p>
  if (!hasPermission("items:delete")) {
    return <p>No permission to delete items</p>
  }

  return <DeleteButton />
}
```

#### usePermissions()
Convenience wrapper around useAuth() for permission checking. Recommended for components.

```tsx
import usePermissions from "@/hooks/usePermissions"

function AdminPanel() {
  const {
    can,       // (permission: string) => boolean
    cannot,    // (permission: string) => boolean
    canAny,    // (...permissions: string[]) => boolean
    canAll,    // (...permissions: string[]) => boolean
    roles,     // User's roles
    permissions, // User's permissions
    loading,   // Is still fetching
    error,     // Any error during fetch
  } = usePermissions()

  if (loading) return <Spinner />
  if (error) return <p>Error: {error}</p>

  // Conditional rendering based on permissions
  return (
    <div>
      {can("users:read") && <UsersList />}
      {can("users:delete") && <DeleteUsersButton />}
      {cannot("admin:manage") && <LockedFeature />}
    </div>
  )
}
```

#### useRequiresPermission()
Hook for requiring a specific permission with loading state.

```tsx
import useRequiresPermission from "@/hooks/useRequiresPermission"

function RestrictedFeature() {
  const { allowed, loading, error } = useRequiresPermission("items:delete")

  if (loading) return <Spinner />
  if (!allowed) return null
  if (error) return <p>Permission check failed</p>

  return <DeleteButton />
}
```

### Permission Checks in Components

**Conditional UI Rendering:**

```tsx
import usePermissions from "@/hooks/usePermissions"

function ItemActions({ itemId }: { itemId: UUID }) {
  const { can } = usePermissions()

  return (
    <div className="space-x-2">
      {can("items:read") && (
        <Button onClick={() => viewItem(itemId)}>View</Button>
      )}
      {can("items:update") && (
        <Button onClick={() => editItem(itemId)}>Edit</Button>
      )}
      {can("items:delete") && (
        <Button variant="destructive" onClick={() => deleteItem(itemId)}>
          Delete
        </Button>
      )}
    </div>
  )
}
```

**Multiple Permission Checks:**

```tsx
const { can, canAny, canAll } = usePermissions()

// At least one permission
if (canAny("items:delete", "items:admin")) {
  // User can delete OR has admin access
}

// All permissions required
if (canAll("items:read", "items:update")) {
  // User can both read AND update items
}
```

**Permission-Based Sidebar Items:**

```tsx
import usePermissions from "@/hooks/usePermissions"

interface Item {
  title: string
  path: string
  permission?: string
}

function Sidebar() {
  const { can, isSuperAdmin } = usePermissions()

  const adminItems: Item[] = [
    { title: "Users", path: "/admin/users", permission: "users:read" },
    { title: "Roles", path: "/admin/roles", permission: "rbac:view_roles" },
    { title: "Permissions", path: "/admin/perms", permission: "rbac:manage_roles" },
  ]

  // Filter items based on permissions
  const visibleItems = adminItems.filter(item => {
    if (!item.permission) return true
    if (isSuperAdmin?.()) return true
    return can(item.permission)
  })

  return (
    <nav>
      {visibleItems.map(item => (
        <Link key={item.path} to={item.path}>{item.title}</Link>
      ))}
    </nav>
  )
}
```

### Route Protection

Use the `createRouteGuard()` utility to protect TanStack Router routes:

```tsx
import { createFileRoute } from "@tanstack/react-router"
import { createRouteGuard } from "@/auth/roleGuard"

// Require specific permissions
export const Route = createFileRoute("/_layout/admin/roles")({
  component: RolesPage,
  beforeLoad: createRouteGuard({
    requiredPermissions: ["rbac:view_roles"],
  }),
})

// Require specific roles (user must have at least one)
export const Route = createFileRoute("/_layout/admin")({
  component: AdminPage,
  beforeLoad: createRouteGuard({
    requiredRoles: ["super_admin", "admin"],
  }),
})

// Require both (all permissions AND at least one role)
export const Route = createFileRoute("/_layout/admin/sensitive")({
  component: SensitivePage,
  beforeLoad: createRouteGuard({
    requiredRoles: ["super_admin"],
    requiredPermissions: ["users:delete", "roles:delete"],
  }),
})
```

**What happens:**
1. Route guard calls `/api/v1/users/me` to get current user
2. If not authenticated → redirect to `/login`
3. If super_admin user → bypass all checks and load route
4. If roles required → fetch `/api/v1/rbac/users/{id}/roles`, check against requirements
5. If permissions required → fetch `/api/v1/rbac/users/{id}/permissions`, check against requirements
6. If requirements not met → redirect to `/unauthorized`
7. If success → load route component

### API Client Integration

The frontend API client is auto-generated from the backend OpenAPI schema and includes service classes for RBAC operations:

```tsx
import { RbacService, UsersService } from "@/client"

// Fetch permissions
const perms = await RbacService.getPermissions({ skip: 0, limit: 100 })

// Fetch roles
const roles = await RbacService.listRoles({ limit: 100 })

// Get user's roles
const userRoles = await RbacService.getUserRolesEndpoint({ userId: user.id })

// Get user's permissions (computed from roles)
const userPerms = await RbacService.getUserPermissionsEndpoint({ userId: user.id })

// Create a role
const newRole = await RbacService.createRole({
  body: {
    name: "editor",
    description: "Can edit items",
    permission_ids: [perm1, perm2],
  },
})

// Assign role to user
await RbacService.assignRoleToUser({
  userId: user.id,
  roleId: role.id,
})
```

### Superuser Bypass

In the frontend, superusers automatically pass all permission checks:

```tsx
const { can, isSuperAdmin } = usePermissions()

// All checks pass for superusers
console.log(can("any:permission"))  // true (if superuser)
console.log(can("another:perm"))    // true (if superuser)
console.log(isSuperAdmin?.())        // true
```

Backend always validates superuser status independently via `user.is_superuser` flag.

---

## Common Patterns

### Admin Panel Sidebar with Conditional Items

```tsx
import usePermissions from "@/hooks/usePermissions"

interface AdminItem {
  icon: React.ReactNode
  title: string
  path: string
  permission: string
}

const adminItems: AdminItem[] = [
  { icon: Users, title: "Users", path: "/admin/users", permission: "users:read" },
  { icon: Shield, title: "Roles", path: "/admin/roles", permission: "rbac:view_roles" },
  { icon: Lock, title: "Permissions", path: "/admin/perms", permission: "rbac:manage_roles" },
]

function AdminSidebar() {
  const { can, isSuperAdmin } = usePermissions()

  const visibleItems = adminItems.filter(item => {
    if (isSuperAdmin?.()) return true
    return can(item.permission)
  })

  return (
    <nav className="space-y-2">
      {visibleItems.map(item => (
        <Link key={item.path} to={item.path} className="flex gap-2">
          {item.icon}
          {item.title}
        </Link>
      ))}
    </nav>
  )
}
```

### Protected Action Buttons

```tsx
import usePermissions from "@/hooks/usePermissions"
import { Button } from "@/components/ui/button"

interface ActionButtonProps {
  permission: string
  onClick: () => void
  children: React.ReactNode
  disabled?: boolean
}

function ProtectedButton({
  permission,
  onClick,
  children,
  disabled = false,
}: ActionButtonProps) {
  const { can } = usePermissions()

  if (!can(permission)) {
    return null  // Hide button entirely
  }

  return (
    <Button onClick={onClick} disabled={disabled}>
      {children}
    </Button>
  )
}

// Usage
<ProtectedButton permission="items:delete" onClick={() => deleteItem()}>
  Delete Item
</ProtectedButton>
```

### Fine-Grained Component Rendering

```tsx
function ItemDetails({ item }: { item: ItemPublic }) {
  const { can } = usePermissions()

  return (
    <div className="space-y-4">
      <h1>{item.title}</h1>
      <p>{item.description}</p>

      {can("items:read") && (
        <div>
          <strong>Created:</strong> {item.created_at}
        </div>
      )}

      {can("items:update") && (
        <button onClick={() => editItem(item.id)}>Edit</button>
      )}

      {can("items:delete") && (
        <button onClick={() => deleteItem(item.id)}>Delete</button>
      )}

      {can("items:admin") && (
        <div className="p-4 bg-yellow-50 border border-yellow-200">
          <h3>Admin Options</h3>
          <button>Reset Item</button>
          <button>Change Owner</button>
        </div>
      )}
    </div>
  )
}
```

---

## Permission Naming Convention

Permissions follow a consistent **resource:action** naming pattern:

```
resource:action

Examples:
  items:read           # Read items
  items:create         # Create new items
  items:update         # Update items
  items:delete         # Delete items
  users:read           # View users
  users:manage         # Full user management
  rbac:view_roles      # View roles
  rbac:manage_roles    # Create/edit/delete roles
  admin:manage_tasks   # Admin task management
```

**Resource Groups:**
- `items:` — Item CRUD operations
- `users:` — User management
- `rbac:` — Role and permission management
- `admin:` — Admin-specific features
- `tasks:` — Task/job management
- Custom resources as needed

---

## Testing RBAC

### Backend Tests

```python
import pytest
from backend.crud_rbac import get_user_roles, user_has_permission

def test_user_with_permission(db_session, test_user, test_role):
    """Test that user with role has its permissions."""
    # Assign role to user
    assign_role_to_user(session=db_session, user_id=test_user.id, role_id=test_role.id)

    # Check user has permission from role
    has_perm = user_has_permission(
        db_session, test_user, "items:read"
    )
    assert has_perm is True

def test_superuser_bypasses_checks(db_session, superuser):
    """Superusers should always have access."""
    # Even to non-existent permissions
    assert user_has_permission(db_session, superuser, "fake:permission")
```

### Frontend Tests (Playwright)

```typescript
// tests/rbac.spec.ts
import { test, expect } from "@playwright/test"
import { admin, regularUser, viewer } from "./auth.setup"

test("Admin can see admin panel", async ({ page, context }) => {
  // Use admin auth context
  await context.addCookies([{ name: "token", value: admin.token }])

  await page.goto("/admin")
  await expect(page.locator("text=Users")).toBeVisible()
  await expect(page.locator("text=Roles")).toBeVisible()
})

test("Viewer cannot see admin panel", async ({ page, context }) => {
  // Use viewer auth context
  await context.addCookies([{ name: "token", value: viewer.token }])

  await page.goto("/admin")
  await expect(page).toHaveURL("/unauthorized")
})

test("Permission check blocks API call", async ({ page, context }) => {
  await context.addCookies([{ name: "token", value: regularUser.token }])

  // Try to delete item without permission
  const response = await page.request.delete("/api/v1/items/123")
  expect(response.status()).toBe(403)
})
```

---

## Troubleshooting

### "Permission Denied" on Protected Route

1. **Check user roles:** `useAuth()` to inspect `roles` array
2. **Check route guard:** Verify `requiredPermissions` or `requiredRoles`
3. **Check backend:** Ensure route is decorated with `@Depends(require_permission(...))`
4. **Check user assignment:** Verify role is assigned to user in admin panel

### Permissions Not Loading

1. **Check auth state:** Is `useAuth()` returning a user?
2. **Check token:** Is JWT token valid and in localStorage?
3. **Check API response:** Inspect network tab for `/api/v1/rbac/users/{id}/permissions`
4. **Check superuser:** Superusers may bypass loading, causing tests to miss state

### Mismatched Frontend/Backend Permissions

1. **Regenerate client:** `cd frontend && bun run generate-client`
2. **Check naming:** Ensure permission names match exactly (case-sensitive)
3. **Sync discovery:** Run `discover_permissions()` to see all found permissions
4. **Check code patterns:** Backend uses `require_permission(...)`, frontend uses `can(...)`

---

## Best Practices

1. **Use permission names in constants:**
   ```tsx
   export const PERMISSIONS = {
     ITEMS_READ: "items:read",
     ITEMS_DELETE: "items:delete",
     USERS_MANAGE: "users:manage",
   } as const

   can(PERMISSIONS.ITEMS_DELETE)  // Type-safe
   ```

2. **Check permissions early:**
   - Route guards: Check before rendering page
   - Components: Check at render time for fast fail
   - API calls: Check before making request to avoid errors

3. **Never trust frontend checks alone:**
   - Always validate on backend via decorators or manual checks
   - Frontend checks are for UX only, not security

4. **Use superuser role for development:**
   ```tsx
   if (isSuperAdmin?.()) {
     // Can see/do everything for testing
   }
   ```

5. **Keep permission names consistent:**
   - Use `resource:action` format consistently
   - Use exact same names in frontend and backend
   - Avoid special characters and spaces

6. **Document permissions:**
   ```python
   @router.delete("/items/{item_id}")
   def delete_item(
       item_id: UUID,
       user: Annotated[User, Depends(require_permission("items:delete"))],
   ):
       """
       Delete an item.

       Required permission: items:delete
       """
   ```

---

## Advanced Topics

### Microsoft Entra Integration

Roles can be synced to Microsoft Entra for SSO integration:

```bash
# Export roles to Entra manifest
GET /api/v1/rbac/roles/entra-manifest

# Response:
{
  "appRoles": [
    {
      "id": "uuid-here",
      "value": "super_admin",
      "displayName": "Super Admin",
      "description": "Application administrator"
    },
    ...
  ]
}
```

Paste into Azure Portal app manifest, then:
- Entra user roles sync to `user.azure_roles` list
- Backend can map Entra roles to app roles for multi-tenancy

### Custom User-Tenant Roles

For multi-tenant SaaS:

```python
class UserTenantRole(SQLModel, table=True):
    """Map users to roles within specific tenants."""
    user_id: UUID
    tenant_id: UUID
    roles: list[str]  # JSON array of role names in this tenant
```

Frontend:
```tsx
const userTenantRoles = await RbacService.getUserTenantRoles({
  userId: user.id,
  tenantId: tenant.id,
})
```

---

## API Reference

See the full RBAC API in `backend/api/routes/rbac.py` for complete endpoint signatures and response schemas.

Hook reference: `frontend/src/hooks/useAuth.ts`, `frontend/src/hooks/usePermissions.ts`
