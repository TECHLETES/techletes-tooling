/**
 * useTasks Hook
 * Manages task enqueueing with React Query.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { TaskCreate, TaskPublic } from "@/client"
import { TasksService } from "@/services"
import useCustomToast from "./useCustomToast"

export interface UseTasksReturn {
  // Mutation
  enqueueTask: (data: TaskCreate) => Promise<TaskPublic>

  // Mutation state
  isCreating: boolean
}

/**
 * Hook for enqueueing background tasks.
 *
 * @example
 * const { enqueueTask, isCreating } = useTasks()
 * const task = await enqueueTask({ task_type: 'email', queue: 'default' })
 */
export function useTasks(): UseTasksReturn {
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()

  // Enqueue mutation
  const enqueueMutation = useMutation({
    mutationFn: (data: TaskCreate) => TasksService.enqueueTask(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "jobStats"] })
      queryClient.invalidateQueries({ queryKey: ["admin", "jobsList"] })
      showSuccessToast("Task enqueued successfully")
    },
    onError: (error: Error) => {
      showErrorToast(error.message)
    },
  })

  return {
    enqueueTask: (data) => enqueueMutation.mutateAsync(data),
    isCreating: enqueueMutation.isPending,
  }
}
