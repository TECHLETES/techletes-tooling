/**
 * App Config Service
 * Business logic wrapper around the app config endpoint.
 */

import type { AppConfig } from "@/client"
import { UtilsService as ApiUtilsService } from "@/client"

export const AppConfigService = {
  /**
   * Fetch runtime application configuration.
   */
  async getAppConfig(): Promise<AppConfig> {
    try {
      return ApiUtilsService.getAppConfig()
    } catch (_error) {
      throw new Error("Failed to load app config")
    }
  },
}
