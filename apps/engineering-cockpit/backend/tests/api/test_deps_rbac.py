"""Tests for RBAC dependency injection functions."""

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from backend.api.deps_rbac import (
    require_all_permissions,
    require_any_role,
    require_permission,
    require_role,
)
from backend.crud_rbac import (
    assign_role_to_user,
    create_permission,
    create_role,
)
from backend.models import PermissionCreate, RoleCreate
from backend.tests.utils.user import create_random_user


class TestRequireRole:
    """Tests for require_role dependency."""

    def test_require_role_with_matching_role(self, db: Session) -> None:
        """Test require_role passes when user has the role."""
        user = create_random_user(db)
        role = create_role(
            session=db,
            role_in=RoleCreate(
                name="admin_test_role",
                description="Admin for testing",
                permission_ids=[],
            ),
        )
        assign_role_to_user(session=db, user_id=user.id, role_id=role.id)

        # Create the dependency
        dependency = require_role("admin_test_role")

        # Call it directly
        result = dependency(current_user=user, session=db)
        assert result.id == user.id

    def test_require_role_without_matching_role(self, db: Session) -> None:
        """Test require_role fails when user lacks the role."""
        user = create_random_user(db)

        # Create the dependency
        dependency = require_role("nonexistent_role")

        # Should raise 403
        with pytest.raises(HTTPException) as exc_info:
            dependency(current_user=user, session=db)

        assert exc_info.value.status_code == 403
        assert "does not have required role" in exc_info.value.detail


class TestRequirePermission:
    """Tests for require_permission dependency."""

    def test_require_permission_with_matching_permission(self, db: Session) -> None:
        """Test require_permission passes when user has the permission."""
        user = create_random_user(db)

        # Create permission
        perm = create_permission(
            session=db,
            permission_in=PermissionCreate(
                name="test:read",
                description="Test read permission",
                resource="test",
            ),
        )

        # Create role with permission
        role = create_role(
            session=db,
            role_in=RoleCreate(
                name="test_perm_role",
                description="Test role",
                permission_ids=[perm.id],
            ),
        )

        # Assign role to user
        assign_role_to_user(session=db, user_id=user.id, role_id=role.id)

        # Create the dependency
        dependency = require_permission("test:read")

        # Should pass
        result = dependency(current_user=user, session=db)
        assert result.id == user.id

    def test_require_permission_without_matching_permission(self, db: Session) -> None:
        """Test require_permission fails when user lacks the permission."""
        user = create_random_user(db)

        # Create the dependency
        dependency = require_permission("nonexistent:permission")

        # Should raise 403
        with pytest.raises(HTTPException) as exc_info:
            dependency(current_user=user, session=db)

        assert exc_info.value.status_code == 403
        assert "does not have required permission" in exc_info.value.detail


class TestRequireAnyRole:
    """Tests for require_any_role dependency."""

    def test_require_any_role_with_one_matching_role(self, db: Session) -> None:
        """Test require_any_role passes when user has one of the roles."""
        user = create_random_user(db)

        # Create role
        role = create_role(
            session=db,
            role_in=RoleCreate(
                name="role_a",
                description="Role A",
                permission_ids=[],
            ),
        )

        # Assign role to user
        assign_role_to_user(session=db, user_id=user.id, role_id=role.id)

        # Create the dependency requiring role_a OR role_b
        dependency = require_any_role("role_a", "role_b")

        # Should pass
        result = dependency(current_user=user, session=db)
        assert result.id == user.id

    def test_require_any_role_without_any_matching_role(self, db: Session) -> None:
        """Test require_any_role fails when user has none of the roles."""
        user = create_random_user(db)

        # Create the dependency requiring role_x OR role_y
        dependency = require_any_role("role_x", "role_y")

        # Should raise 403
        with pytest.raises(HTTPException) as exc_info:
            dependency(current_user=user, session=db)

        assert exc_info.value.status_code == 403
        assert "does not have any of required roles" in exc_info.value.detail

    def test_require_any_role_with_multiple_matching_roles(self, db: Session) -> None:
        """Test require_any_role passes when user has multiple of the roles."""
        user = create_random_user(db)

        # Create two roles
        role_a = create_role(
            session=db,
            role_in=RoleCreate(
                name="multi_role_a",
                description="Multi Role A",
                permission_ids=[],
            ),
        )
        role_b = create_role(
            session=db,
            role_in=RoleCreate(
                name="multi_role_b",
                description="Multi Role B",
                permission_ids=[],
            ),
        )

        # Assign both roles to user
        assign_role_to_user(session=db, user_id=user.id, role_id=role_a.id)
        assign_role_to_user(session=db, user_id=user.id, role_id=role_b.id)

        # Create the dependency
        dependency = require_any_role("multi_role_a", "multi_role_b", "multi_role_c")

        # Should pass
        result = dependency(current_user=user, session=db)
        assert result.id == user.id


class TestRequireAllPermissions:
    """Tests for require_all_permissions dependency."""

    def test_require_all_permissions_with_all_permissions(self, db: Session) -> None:
        """Test require_all_permissions passes when user has all permissions."""
        user = create_random_user(db)

        # Create multiple permissions
        perm1 = create_permission(
            session=db,
            permission_in=PermissionCreate(
                name="resource:create",
                description="Create resource",
                resource="resource",
            ),
        )
        perm2 = create_permission(
            session=db,
            permission_in=PermissionCreate(
                name="resource:update",
                description="Update resource",
                resource="resource",
            ),
        )

        # Create role with all permissions
        role = create_role(
            session=db,
            role_in=RoleCreate(
                name="full_access_role",
                description="Full access",
                permission_ids=[perm1.id, perm2.id],
            ),
        )

        # Assign role to user
        assign_role_to_user(session=db, user_id=user.id, role_id=role.id)

        # Create the dependency requiring both
        dependency = require_all_permissions("resource:create", "resource:update")

        # Should pass
        result = dependency(current_user=user, session=db)
        assert result.id == user.id

    def test_require_all_permissions_without_some_permissions(
        self, db: Session
    ) -> None:
        """Test require_all_permissions fails when user lacks any permission."""
        user = create_random_user(db)

        # Create one permission
        perm1 = create_permission(
            session=db,
            permission_in=PermissionCreate(
                name="partial:read",
                description="Partial read",
                resource="partial",
            ),
        )

        # Create role with only one permission
        role = create_role(
            session=db,
            role_in=RoleCreate(
                name="partial_role",
                description="Partial access",
                permission_ids=[perm1.id],
            ),
        )

        # Assign role to user
        assign_role_to_user(session=db, user_id=user.id, role_id=role.id)

        # Create the dependency requiring both permissions
        dependency = require_all_permissions("partial:read", "partial:write")

        # Should raise 403
        with pytest.raises(HTTPException) as exc_info:
            dependency(current_user=user, session=db)

        assert exc_info.value.status_code == 403
        assert "missing required permissions" in exc_info.value.detail
        assert "partial:write" in exc_info.value.detail

    def test_require_all_permissions_without_any_permissions(self, db: Session) -> None:
        """Test require_all_permissions fails when user has no permissions."""
        user = create_random_user(db)

        # Create the dependency without assigning any role
        dependency = require_all_permissions("admin:delete", "admin:manage")

        # Should raise 403
        with pytest.raises(HTTPException) as exc_info:
            dependency(current_user=user, session=db)

        assert exc_info.value.status_code == 403
        assert "missing required permissions" in exc_info.value.detail
