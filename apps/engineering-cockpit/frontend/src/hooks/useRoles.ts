/**
 * useRoles Hook
 * Manages role and permission data fetching with React Query.
 * Provides loading states, error handling, and cache management.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"
import type {
  PermissionPublic,
  RoleCreate,
  RolePublic,
  RoleUpdate,
} from "@/client"
import { RolesService } from "@/services"
import useCustomToast from "./useCustomToast"

export interface UseRolesOptions {
  skip?: number
  limit?: number
  enabled?: boolean
}

export interface UseRolesReturn {
  // Query data
  roles: RolePublic[]
  permissions: PermissionPublic[]
  total: number
  hasMore: boolean
  isLoading: boolean
  isLoadingPermissions: boolean
  error: Error | null
  permissionsError: Error | null

  // Mutations
  createRole: (data: RoleCreate) => Promise<RolePublic>
  updateRole: (roleId: string, data: Partial<RoleUpdate>) => Promise<RolePublic>
  deleteRole: (roleId: string) => Promise<boolean>
  assignRoleToUser: (userId: string, roleId: string) => Promise<boolean>
  removeRoleFromUser: (userId: string, roleId: string) => Promise<boolean>

  // Mutation states
  isCreating: boolean
  isUpdating: boolean
  isDeleting: boolean
  isAssigning: boolean
}

/**
 * Hook for managing roles and permissions with React Query.
 * Handles fetching, creating, updating, and deleting roles and permissions.
 *
 * @example
 * const { roles, permissions, createRole } = useRoles()
 * const { roles } = useRoles({ skip: 10, limit: 20 })
 */
export function useRoles(options?: UseRolesOptions): UseRolesReturn {
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const { t } = useTranslation()

  const skip = options?.skip ?? 0
  const limit = options?.limit ?? 10
  const enabled = options?.enabled ?? true

  // Fetch roles
  const {
    data: rolesData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["roles", { skip, limit }],
    queryFn: () => RolesService.listRoles(skip, limit),
    enabled,
    staleTime: 60000, // 60 seconds
  })

  // Fetch permissions
  const {
    data: permissionsData,
    isLoading: isLoadingPermissions,
    error: permissionsError,
  } = useQuery({
    queryKey: ["permissions"],
    queryFn: () => RolesService.listPermissions(),
    enabled,
    staleTime: 60000, // 60 seconds
  })

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: RoleCreate) => RolesService.createRole(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["roles"] })
      showSuccessToast(t("roles.feedback.created"))
    },
    onError: (error: Error) => {
      showErrorToast(error.message)
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({
      roleId,
      data,
    }: {
      roleId: string
      data: Partial<RoleUpdate>
    }) => RolesService.updateRole(roleId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["roles"] })
      showSuccessToast(t("roles.feedback.updated"))
    },
    onError: (error: Error) => {
      showErrorToast(error.message)
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (roleId: string) => RolesService.deleteRole(roleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["roles"] })
      showSuccessToast(t("roles.feedback.deleted"))
    },
    onError: (error: Error) => {
      showErrorToast(error.message)
    },
  })

  // Assign role mutation
  const assignMutation = useMutation({
    mutationFn: ({ userId, roleId }: { userId: string; roleId: string }) =>
      RolesService.assignRoleToUser(userId, roleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
      queryClient.invalidateQueries({ queryKey: ["currentUser"] })
      showSuccessToast(t("roles.feedback.assigned"))
    },
    onError: (error: Error) => {
      showErrorToast(error.message)
    },
  })

  // Remove role mutation
  const removeMutation = useMutation({
    mutationFn: ({ userId, roleId }: { userId: string; roleId: string }) =>
      RolesService.removeRoleFromUser(userId, roleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
      queryClient.invalidateQueries({ queryKey: ["currentUser"] })
      showSuccessToast(t("roles.feedback.removed"))
    },
    onError: (error: Error) => {
      showErrorToast(error.message)
    },
  })

  return {
    roles: rolesData?.roles ?? [],
    permissions: permissionsData?.permissions ?? [],
    total: rolesData?.total ?? 0,
    hasMore: rolesData?.hasMore ?? false,
    isLoading,
    isLoadingPermissions,
    error: error as Error | null,
    permissionsError: permissionsError as Error | null,

    createRole: (data) => createMutation.mutateAsync(data),
    updateRole: (roleId, data) => updateMutation.mutateAsync({ roleId, data }),
    deleteRole: (roleId) => deleteMutation.mutateAsync(roleId),
    assignRoleToUser: (userId, roleId) =>
      assignMutation.mutateAsync({ userId, roleId }),
    removeRoleFromUser: (userId, roleId) =>
      removeMutation.mutateAsync({ userId, roleId }),

    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
    isAssigning: assignMutation.isPending || removeMutation.isPending,
  }
}
