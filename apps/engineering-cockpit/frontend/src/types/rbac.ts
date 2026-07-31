/**
 * RBAC Type definitions for frontend.
 * These types are used internally for type safety and convenience.
 * The actual types are imported from the auto-generated client.
 */

import type { PermissionPublic, RolePublic } from "@/client"

export type Role = RolePublic
export type Permission = PermissionPublic

/**
 * User roles and permissions context.
 * Used to track loaded state and provide permission checking utilities.
 */
export interface UserRoleContext {
  roles: Role[]
  permissions: Permission[]
  isLoading: boolean
  error: string | null
}
