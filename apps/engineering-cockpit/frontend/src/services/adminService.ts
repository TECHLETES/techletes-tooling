/**
 * Admin Service
 * Business logic wrapper around Admin API client.
 * Handles admin operations, statistics, and job management.
 */

import type { JobsListResponse, JobsStatsResponse } from "@/client"
import { AdminService as ApiAdminService } from "@/client"

export const AdminService = {
  /**
   * Get admin job statistics.
   *
   * @returns Object with job statistics
   */
  async getJobsStats(): Promise<JobsStatsResponse> {
    try {
      const stats = (await ApiAdminService.getJobsStats()) as JobsStatsResponse
      return stats
    } catch (_error) {
      throw new Error("Failed to fetch job statistics")
    }
  },

  /**
   * Get list of recent jobs.
   *
   * @param query - Query parameters (e.g., limit, offset)
   * @returns Object with jobs list
   */
  async getJobsList(
    query?: Record<string, unknown>,
  ): Promise<JobsListResponse> {
    try {
      const jobs = (await ApiAdminService.getJobsList(
        query,
      )) as JobsListResponse
      return jobs
    } catch (_error) {
      throw new Error("Failed to fetch jobs list")
    }
  },
}
