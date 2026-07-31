/**
 * useItems Hook
 * Manages item data fetching and mutations with React Query.
 * Provides loading states, error handling, and cache management.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"
import type { ItemCreate, ItemPublic, ItemUpdate } from "@/client"
import { ItemsService } from "@/services"
import useCustomToast from "./useCustomToast"

export interface UseItemsOptions {
  skip?: number
  limit?: number
  enabled?: boolean
}

export interface UseItemsReturn {
  // Query data
  items: ItemPublic[]
  total: number
  hasMore: boolean
  isLoading: boolean
  error: Error | null

  // Mutations
  createItem: (data: ItemCreate) => Promise<ItemPublic>
  updateItem: (itemId: string, data: Partial<ItemUpdate>) => Promise<ItemPublic>
  deleteItem: (itemId: string) => Promise<boolean>
  batchDelete: (
    itemIds: string[],
  ) => Promise<{ succeeded: number; failed: number }>

  // Mutation states
  isCreating: boolean
  isUpdating: boolean
  isDeleting: boolean
}

/**
 * Hook for managing items with React Query.
 * Handles fetching, creating, updating, and deleting items.
 *
 * @example
 * const { items, isLoading, createItem } = useItems()
 * const { items, error } = useItems({ skip: 10, limit: 20 })
 */
export function useItems(options?: UseItemsOptions): UseItemsReturn {
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const { t } = useTranslation()

  const skip = options?.skip ?? 0
  const limit = options?.limit ?? 10
  const enabled = options?.enabled ?? true

  // Fetch items
  const {
    data: itemsData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["items", { skip, limit }],
    queryFn: () => ItemsService.listItems(skip, limit),
    enabled,
    staleTime: 30000, // 30 seconds
  })

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: ItemCreate) => ItemsService.createItem(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["items"] })
      showSuccessToast(t("items.feedback.created"))
    },
    onError: (error: Error) => {
      showErrorToast(error.message)
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({
      itemId,
      data,
    }: {
      itemId: string
      data: Partial<ItemUpdate>
    }) => ItemsService.updateItem(itemId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["items"] })
      showSuccessToast(t("items.feedback.updated"))
    },
    onError: (error: Error) => {
      showErrorToast(error.message)
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (itemId: string) => ItemsService.deleteItem(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["items"] })
      showSuccessToast(t("items.feedback.deleted"))
    },
    onError: (error: Error) => {
      showErrorToast(error.message)
    },
  })

  // Batch delete mutation
  const batchDeleteMutation = useMutation({
    mutationFn: (itemIds: string[]) => ItemsService.batchDelete(itemIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["items"] })
      showSuccessToast(t("items.feedback.batchDeleted"))
    },
    onError: (error: Error) => {
      showErrorToast(error.message)
    },
  })

  return {
    items: itemsData?.items ?? [],
    total: itemsData?.total ?? 0,
    hasMore: itemsData?.hasMore ?? false,
    isLoading,
    error: error as Error | null,

    createItem: (data) => createMutation.mutateAsync(data),
    updateItem: (itemId, data) => updateMutation.mutateAsync({ itemId, data }),
    deleteItem: (itemId) => deleteMutation.mutateAsync(itemId),
    batchDelete: (itemIds) => batchDeleteMutation.mutateAsync(itemIds),

    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending || batchDeleteMutation.isPending,
  }
}
