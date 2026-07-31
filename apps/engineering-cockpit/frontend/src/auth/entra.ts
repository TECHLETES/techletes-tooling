import {
  type Configuration,
  LogLevel,
  PublicClientApplication,
} from "@azure/msal-browser"

import type { EntraProviderConfig } from "@/client"
import { AuthService } from "@/services"

type EntraConfig = EntraProviderConfig

let msalInstance: PublicClientApplication | null = null
let entraConfig: EntraConfig | null = null

export const loginScopes = ["openid", "profile", "email"]

export const isEntraEnabled = (): boolean => {
  return Boolean(entraConfig?.client_id)
}

export const getMsalInstance = (): PublicClientApplication => {
  if (!msalInstance) {
    throw new Error("MSAL not initialized. Call initEntra() first.")
  }
  return msalInstance
}

export const initEntra = async (
  preloadedConfig?: EntraConfig | null,
): Promise<void> => {
  try {
    if (preloadedConfig) {
      // Use preloaded config from consolidated endpoint
      entraConfig = preloadedConfig
    } else {
      // Fallback: fetch individual endpoint if needed
      entraConfig = await AuthService.getEntraConfig()
    }

    if (!entraConfig?.client_id) return

    const msalConfig: Configuration = {
      auth: {
        clientId: entraConfig.client_id,
        authority: entraConfig.authority ?? undefined,
        redirectUri: window.location.origin,
        postLogoutRedirectUri: "/",
      },
      cache: {
        cacheLocation: "localStorage",
      },
      system: {
        loggerOptions: {
          loggerCallback: (_level, message) => {
            if (_level === LogLevel.Error) console.error(message)
          },
          logLevel: LogLevel.Error,
        },
      },
    }

    msalInstance = new PublicClientApplication(msalConfig)
  } catch (error) {
    console.error("Failed to initialize Entra:", error)
  }
}
