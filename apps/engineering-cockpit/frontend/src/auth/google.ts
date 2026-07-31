import {
  GoogleOAuthProvider,
  type TokenResponse,
  useGoogleLogin,
} from "@react-oauth/google"

import type { GoogleProviderConfig } from "@/client"
import { AuthService } from "@/services"

type GoogleConfig = GoogleProviderConfig

let googleConfig: GoogleConfig | null = null

export const isGoogleEnabled = (): boolean => {
  return Boolean(googleConfig?.client_id)
}

export const getGoogleConfig = (): GoogleConfig => {
  if (!googleConfig) {
    throw new Error("Google config not initialized. Call initGoogle() first.")
  }
  return googleConfig
}

export const initGoogle = async (
  preloadedConfig?: GoogleConfig | null,
): Promise<void> => {
  try {
    if (preloadedConfig) {
      // Use preloaded config from consolidated endpoint
      googleConfig = preloadedConfig
    } else {
      // Fallback: fetch individual endpoint if needed
      googleConfig = await AuthService.getGoogleConfig()
    }
  } catch (error) {
    console.error("Failed to initialize Google config:", error)
    googleConfig = { enabled: false, client_id: null }
  }
}

export const useGoogleSignIn = () => {
  const login = useGoogleLogin({
    onSuccess: (tokenResponse: TokenResponse) => {
      return tokenResponse
    },
  })

  return login
}

export { GoogleOAuthProvider }
