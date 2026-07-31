/**
 * Consolidated authentication configuration initialization.
 * Fetches all auth provider configs in a single API call for optimal performance.
 */

import type { ConsolidatedAuthConfig } from "@/client"
import { AuthService } from "@/services"

let cachedConfig: ConsolidatedAuthConfig | null = null

/**
 * Fetch consolidated auth configuration from the backend.
 * This replaces multiple individual endpoint calls with a single call.
 */
export async function loadConsolidatedAuthConfig(): Promise<ConsolidatedAuthConfig> {
  if (cachedConfig) {
    return cachedConfig
  }

  try {
    const config = await AuthService.getConsolidatedConfig()
    cachedConfig = config
    return config
  } catch (error) {
    console.error("Failed to load consolidated auth config:", error)
    // Return safe defaults
    return {
      entra: {
        enabled: false,
        client_id: null,
        tenant_id: null,
        authority: null,
      },
      google: { enabled: false, client_id: null },
      github: { enabled: false, client_id: null },
      app: { signup_enabled: false },
    }
  }
}

export function getConsolidatedAuthConfig(): ConsolidatedAuthConfig | null {
  return cachedConfig
}
