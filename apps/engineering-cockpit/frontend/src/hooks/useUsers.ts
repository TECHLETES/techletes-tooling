/**
 * useUsers Hook
 * Manages user data fetching and mutations with React Query.
 * Provides loading states, error handling, and cache management.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"
import type { UserCreate, UserPublic, UserUpdate, UserUpdateMe } from "@/client"
import { UsersService } from "@/services"
import useCustomToast from "./useCustomToast"

export interface UseUsersOptions {
  skip?: number
  limit?: number
  enabled?: boolean
}

export interface UseUsersReturn {
  // Query data
  users: UserPublic[]
  total: number
  hasMore: boolean
  isLoading: boolean
  error: Error | null

  // Mutations
  createUser: (data: UserCreate) => Promise<UserPublic>
  updateUser: (userId: string, data: Partial<UserUpdate>) => Promise<UserPublic>
  updateCurrentUser: (data: Partial<UserUpdateMe>) => Promise<UserPublic>
  deleteUser: (userId: string) => Promise<boolean>
  batchDelete: (
    userIds: string[],
  ) => Promise<{ succeeded: number; failed: number }>

  // Mutation states
  isCreating: boolean
  isUpdating: boolean
  isDeleting: boolean
}

/**
 * Hook for managing users with React Query.
 * Handles fetching, creating, updating, and deleting users.
 *
 * @example
 * const { users, isLoading, createUser } = useUsers()
 * const { users } = useUsers({ skip: 10, limit: 20 })
 */
export function useUsers(options?: UseUsersOptions): UseUsersReturn {
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const { t } = useTranslation()

  const skip = options?.skip ?? 0
  const limit = options?.limit ?? 10
  const enabled = options?.enabled ?? true

  // Fetch users
  const {
    data: usersData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["users", { skip, limit }],
    queryFn: () => UsersService.listUsers(skip, limit),
    enabled,
    staleTime: 30000, // 30 seconds
  })

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: UserCreate) => UsersService.createUser(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
      showSuccessToast(t("users.feedback.created"))
    },
    onError: (error: Error) => {
      showErrorToast(error.message)
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({
      userId,
      data,
    }: {
      userId: string
      data: Partial<UserUpdate>
    }) => UsersService.updateUser(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
      queryClient.invalidateQueries({ queryKey: ["currentUser"] })
      showSuccessToast(t("users.feedback.updated"))
    },
    onError: (error: Error) => {
      showErrorToast(error.message)
    },
  })

  // Update current user mutation
  const updateCurrentMutation = useMutation({
    mutationFn: (data: Partial<UserUpdateMe>) =>
      UsersService.updateCurrentUser(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["currentUser"] })
      showSuccessToast(t("users.feedback.profileUpdated"))
    },
    onError: (error: Error) => {
      showErrorToast(error.message)
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (userId: string) => UsersService.deleteUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
      showSuccessToast(t("users.feedback.deleted"))
    },
    onError: (error: Error) => {
      showErrorToast(error.message)
    },
  })

  // Batch delete mutation
  const batchDeleteMutation = useMutation({
    mutationFn: (userIds: string[]) => UsersService.batchDelete(userIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
      showSuccessToast(t("users.feedback.batchDeleted"))
    },
    onError: (error: Error) => {
      showErrorToast(error.message)
    },
  })

  return {
    users: usersData?.users ?? [],
    total: usersData?.total ?? 0,
    hasMore: usersData?.hasMore ?? false,
    isLoading,
    error: error as Error | null,

    createUser: (data) => createMutation.mutateAsync(data),
    updateUser: (userId, data) => updateMutation.mutateAsync({ userId, data }),
    updateCurrentUser: (data) => updateCurrentMutation.mutateAsync(data),
    deleteUser: (userId) => deleteMutation.mutateAsync(userId),
    batchDelete: (userIds) => batchDeleteMutation.mutateAsync(userIds),

    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending || updateCurrentMutation.isPending,
    isDeleting: deleteMutation.isPending || batchDeleteMutation.isPending,
  }
}
