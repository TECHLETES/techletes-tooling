import { useQuery } from "@tanstack/react-query"
import { getConsolidatedAuthConfig } from "@/auth/consolidatedConfig"
import { AppConfigService } from "@/services"

const useAppConfig = () => {
  // Try to get app config from consolidated auth config first
  const consolidatedConfig = getConsolidatedAuthConfig()

  const {
    data: config,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["appConfig"],
    // Use consolidated config if available, otherwise fetch from individual endpoint
    queryFn: async () => {
      if (consolidatedConfig?.app) {
        return consolidatedConfig.app
      }
      return AppConfigService.getAppConfig()
    },
    // Don't refetch if we already have the data from consolidated config
    staleTime: consolidatedConfig?.app ? Infinity : 0,
  })

  return {
    config,
    isLoading,
    error,
  }
}

export default useAppConfig
