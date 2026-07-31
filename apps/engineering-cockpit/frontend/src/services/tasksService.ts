/**
 * Tasks Service
 * Business logic wrapper around Tasks API client.
 * Enqueues background tasks for processing.
 */

import type { TaskCreate, TaskPublic } from "@/client"
import { TasksService as ApiTasksService } from "@/client"

export const TasksService = {
  /**
   * Enqueue a new task to be processed.
   *
   * @param data - Task creation data (task_type, queue, kwargs)
   * @returns Enqueued task/job info
   */
  async enqueueTask(data: TaskCreate): Promise<TaskPublic> {
    try {
      const enqueued = await ApiTasksService.enqueueTask({
        requestBody: data,
      })
      return enqueued
    } catch (_error) {
      throw new Error("Failed to enqueue task")
    }
  },
}
