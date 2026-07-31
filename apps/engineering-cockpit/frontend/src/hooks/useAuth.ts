import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import type { AxiosError } from "axios"

import {
  type Body_login_login_access_token as AccessToken,
  ApiError,
  type PermissionPublic,
  type RolePublic,
  type UserPublic,
  type UserRegister,
} from "@/client"
import { clearSessionMarker, hasSessionMarker } from "@/lib/session"
import { AuthService, RolesService, UsersService } from "@/services"
import useCustomToast from "./useCustomToast"

const isLoggedIn = () => {
  return hasSessionMarker()
}

const useAuth = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showErrorToast } = useCustomToast()

  const { data: user, error } = useQuery<UserPublic | null, AxiosError>({
    queryKey: ["currentUser"],
    queryFn: async () => (await UsersService.getCurrentUser()) ?? null,
    enabled: isLoggedIn(),
    retry: false,
  })

  // Handle 404 on readUserMe: session is no longer valid
  if (
    error instanceof ApiError &&
    error.response?.status === 404 &&
    isLoggedIn()
  ) {
    // Clear all session data
    sessionStorage.clear()
    clearSessionMarker()
    // Clear all cookies
    const cookies = document.cookie.split(";")
    cookies.forEach((c) => {
      const name = c.split("=")[0].trim()
      if (name) {
        // biome-ignore lint/suspicious/noDocumentCookie: Cookie clearing is necessary for logout
        document.cookie = `${name}=;expires=${new Date().toUTCString()};path=/`
      }
    })
    // Redirect to login
    navigate({ to: "/login" })
  }

  const signUpMutation = useMutation({
    mutationFn: (data: UserRegister) => UsersService.registerUser(data),
    onSuccess: () => {
      navigate({ to: "/login" })
    },
    onError: (error: Error) => showErrorToast(error.message),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const login = async (data: AccessToken) => {
    await AuthService.loginWithAccessToken(data)
  }

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["currentUser"] })
      navigate({ to: "/" })
    },
    onError: (error: Error) => showErrorToast(error.message),
  })

  // Fetch user roles
  const { data: rolesResponse } = useQuery<RolePublic[], AxiosError>({
    queryKey: ["userRoles", user?.id],
    queryFn: () => (user?.id ? RolesService.getUserRoles(user.id) : []),
    enabled: !!user?.id,
    retry: false,
  })

  // Fetch user permissions
  const { data: permissionsResponse } = useQuery<
    PermissionPublic[],
    AxiosError
  >({
    queryKey: ["userPermissions", user?.id],
    queryFn: () => (user?.id ? RolesService.getUserPermissions(user.id) : []),
    enabled: !!user?.id,
    retry: false,
  })

  const roles = rolesResponse ?? []
  const permissions = permissionsResponse ?? []

  const logout = async () => {
    try {
      await AuthService.logout()
    } finally {
      clearSessionMarker()
    }
    navigate({ to: "/login" })
  }

  /**
   * Check if user has a specific role by name.
   * Case-sensitive comparison.
   */
  const hasRole = (roleName: string): boolean => {
    return roles.some((role: RolePublic) => role.name === roleName)
  }

  /**
   * Check if user has a specific permission by name.
   * Superusers bypass all permission checks.
   * Case-sensitive comparison.
   */
  const hasPermission = (permissionName: string): boolean => {
    // Superusers have all permissions
    if (user?.is_superuser) return true
    if (hasRole("super_admin")) return true

    return permissions.some(
      (perm: PermissionPublic) => perm.name === permissionName,
    )
  }

  /**
   * Check if user has ANY of the provided roles.
   * Superusers have all roles.
   */
  const hasAnyRole = (...roleNames: string[]): boolean => {
    if (user?.is_superuser) return true
    return roleNames.some((roleName) => hasRole(roleName))
  }

  /**
   * Check if user has ALL of the provided permissions.
   * Superusers have all permissions.
   */
  const hasAllPermissions = (...permissionNames: string[]): boolean => {
    if (user?.is_superuser) return true
    return permissionNames.every((permName) => hasPermission(permName))
  }

  /**
   * Check if user is a Super admin.
   */
  const isSuperAdmin = (): boolean => {
    return !!user?.is_superuser || hasRole("super_admin")
  }

  /**
   * Alias for hasPermission() for convenience.
   */
  const canAccess = (permission: string): boolean => {
    return hasPermission(permission)
  }

  return {
    signUpMutation,
    loginMutation,
    logout,
    user,
    roles,
    permissions,
    hasRole,
    hasPermission,
    hasAnyRole,
    hasAllPermissions,
    isSuperAdmin,
    canAccess,
  }
}

export { isLoggedIn }
export default useAuth
