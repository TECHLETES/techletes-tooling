/**
 * Custom hook for permission checking.
 * Wraps useAuth and provides convenience methods for checking permissions.
 */

import useAuth from "./useAuth"

export interface UsePermissionsReturn {
  /**
   * Check if user has a specific permission.
   */
  can: (permission: string) => boolean

  /**
   * Check if user does NOT have a specific permission.
   */
  cannot: (permission: string) => boolean

  /**
   * Check if user has ANY of the provided permissions.
   */
  canAny: (...permissions: string[]) => boolean

  /**
   * Check if user has ALL of the provided permissions.
   */
  canAll: (...permissions: string[]) => boolean

  /**
   * List of user's roles.
   */
  roles: Array<{
    id: string
    name: string
    description?: string | null
    is_system?: boolean
  }>

  /**
   * List of user's permissions.
   */
  permissions: Array<{
    id: string
    name: string
    resource: string
    description?: string | null
  }>

  /**
   * Whether roles/permissions are still loading from API.
   */
  loading: boolean

  /**
   * Error loading roles/permissions (if any).
   */
  error: string | null
}

/**
 * Custom hook for permission and role checking.
 * Primary hook to use in components for permission checks.
 *
 * @example
 * const perms = usePermissions()
 * if (!perms.can('reports:view')) return null
 *
 * @example
 * const perms = usePermissions()
 * if (perms.cannot('users:delete')) {
 *   return <p>You don't have permission to delete users</p>
 * }
 *
 * @returns Permission checking utilities and loading state
 */
function usePermissions(): UsePermissionsReturn {
  const auth = useAuth()

  // Determine loading state - roles/permissions are loaded when user exists and array is populated
  const loading =
    !!auth.user && auth.roles.length === 0 && auth.permissions.length === 0

  return {
    can: (permission: string) => auth.hasPermission(permission),
    cannot: (permission: string) => !auth.hasPermission(permission),
    canAny: (...permissions: string[]) => {
      return permissions.some((perm) => auth.hasPermission(perm))
    },
    canAll: (...permissions: string[]) =>
      auth.hasAllPermissions(...permissions),
    roles: auth.roles,
    permissions: auth.permissions,
    loading,
    error: null,
  }
}

export default usePermissions
