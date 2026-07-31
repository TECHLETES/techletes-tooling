/**
 * useAdmin Hook
 * Manages admin data fetching (statistics, jobs) with React Query.
 * Provides loading states and error handling.
 */

import { useQuery } from "@tanstack/react-query"
import type { JobsListResponse, JobsStatsResponse } from "@/client"
import { AdminService } from "@/services"

export interface UseAdminOptions {
  enabled?: boolean
  refetchInterval?: number
}

export interface UseAdminReturn {
  // Job statistics
  jobStats: JobsStatsResponse | null
  isLoadingJobStats: boolean
  jobStatsError: Error | null

  // Jobs list
  jobsList: JobsListResponse | null
  isLoadingJobsList: boolean
  jobsListError: Error | null

  // Combined state
  isLoading: boolean
  error: Error | null
}

/**
 * Hook for fetching admin data (statistics and jobs) with React Query.
 * Manages job statistics and jobs list.
 *
 * @example
 * const { jobStats, jobsList, isLoading } = useAdmin()
 */
export function useAdmin(options?: UseAdminOptions): UseAdminReturn {
  const enabled = options?.enabled ?? true
  const refetchInterval = options?.refetchInterval

  // Fetch job statistics
  const {
    data: jobStats,
    isLoading: isLoadingJobStats,
    error: jobStatsError,
  } = useQuery({
    queryKey: ["admin", "jobStats"],
    queryFn: () => AdminService.getJobsStats(),
    enabled,
    staleTime: 60000, // 60 seconds
    refetchInterval,
  })

  // Fetch jobs list
  const {
    data: jobsList,
    isLoading: isLoadingJobsList,
    error: jobsListError,
  } = useQuery({
    queryKey: ["admin", "jobsList"],
    queryFn: () => AdminService.getJobsList(),
    enabled,
    staleTime: 60000, // 60 seconds
  })

  return {
    jobStats: jobStats ?? null,
    isLoadingJobStats,
    jobStatsError: jobStatsError as Error | null,

    jobsList: jobsList ?? null,
    isLoadingJobsList,
    jobsListError: jobsListError as Error | null,

    isLoading: isLoadingJobStats || isLoadingJobsList,
    error: (jobStatsError || jobsListError) as Error | null,
  }
}
