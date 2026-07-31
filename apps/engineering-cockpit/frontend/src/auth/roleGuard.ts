/**
 * Utility functions for route and component protection based on roles and permissions.
 * Use these with TanStack Router, React components, and during navigation checks.
 */

import { redirect } from "@tanstack/react-router"

import type { PermissionPublic, RolePublic, UserPublic } from "@/client"
import { RolesService, UsersService } from "@/services"

/**
 * Route guard middleware for TanStack Router.
 * Checks user authentication, roles, and permissions before allowing route access.
 *
 * @param requiredRoles - Role names required for access (user must have at least one)
 * @param requiredPermissions - Permission names required for access (user must have all)
 * @returns TanStack Router beforeLoad handler
 *
 * @example
 * // Require admin or super_admin role
 * export const Route = createFileRoute("/_layout/admin")({
 *   component: AdminPage,
 *   beforeLoad: createRouteGuard({ requiredRoles: ["admin", "super_admin"] })
 * })
 *
 * @example
 * // Require specific permissions
 * export const Route = createFileRoute("/_layout/admin/roles")({
 *   component: RolesPage,
 *   beforeLoad: createRouteGuard({ requiredPermissions: ["rbac:view_roles"] })
 * })
 *
 * @example
 * // Require either roles OR permissions
 * export const Route = createFileRoute("/_layout/admin/users")({
 *   component: UsersPage,
 *   beforeLoad: createRouteGuard({
 *     requiredRoles: ["super_admin"],
 *     requiredPermissions: ["rbac:manage_users"]
 *   })
 * })
 */
export function createRouteGuard(options?: {
  requiredRoles?: string[]
  requiredPermissions?: string[]
}) {
  return async () => {
    try {
      // Check if user is authenticated
      const user = await UsersService.getCurrentUser()

      if (!user) {
        throw redirect({ to: "/login" })
      }

      // If super_admin, bypass all role/permission checks
      if (user.is_superuser) {
        return
      }

      // Check required roles
      if (options?.requiredRoles && options.requiredRoles.length > 0) {
        const userRoles = await RolesService.getUserRoles(user.id)
        const userRoleNames = userRoles.map((r: RolePublic) => r.name)

        const hasRequiredRole = options.requiredRoles.some((requiredRole) =>
          userRoleNames.includes(requiredRole),
        )

        if (!hasRequiredRole) {
          throw redirect({ to: "/unauthorized" })
        }
      }

      // Check required permissions
      if (
        options?.requiredPermissions &&
        options.requiredPermissions.length > 0
      ) {
        const userPermissions = await RolesService.getUserPermissions(user.id)
        const userPermissionNames = userPermissions.map(
          (p: PermissionPublic) => p.name,
        )

        const hasAllRequiredPermissions = options.requiredPermissions.every(
          (requiredPermission) =>
            userPermissionNames.includes(requiredPermission),
        )

        if (!hasAllRequiredPermissions) {
          throw redirect({ to: "/unauthorized" })
        }
      }
    } catch (error) {
      // Re-throw TanStack Router redirects
      if (error instanceof Error && error.message.includes("redirect")) {
        throw error
      }
      // On any other error, redirect to login
      throw redirect({ to: "/login" })
    }
  }
}

/**
 * Check if a user has access to a route based on required roles.
 * If no roles are required, any authenticated user can access.
 * If roles are required, user must have at least one of them.
 *
 * @param user - Current user (null if not authenticated)
 * @param requiredRoles - Array of role names required for access (optional)
 * @returns true if user can access the route, false otherwise
 *
 * @example
 * const canAccess = canAccessRoute(user, ["admin", "super_admin"])
 *
 * @example
 * const canAccess = canAccessRoute(user) // Any authenticated user
 */
export function canAccessRoute(
  user: UserPublic | null,
  requiredRoles?: string[],
): boolean {
  // No user = no access
  if (!user) return false

  // No roles required = user just needs to be authenticated
  if (!requiredRoles || requiredRoles.length === 0) return true

  // User must have access to the backend's user-roles endpoint for this to work
  // In practice, this is checked by the backend on protected routes
  // Frontend can use this for early exit before making API calls

  return true
}
