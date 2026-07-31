import type { GitHubProviderConfig } from "@/client"
import { AuthService } from "@/services"

type GitHubConfig = GitHubProviderConfig

let githubConfig: GitHubConfig | null = null

export const isGithubEnabled = (): boolean => {
  return Boolean(githubConfig?.client_id)
}

export const getGithubConfig = (): GitHubConfig => {
  if (!githubConfig) {
    throw new Error("GitHub config not initialized. Call initGithub() first.")
  }
  return githubConfig
}

export const initGithub = async (
  preloadedConfig?: GitHubConfig | null,
): Promise<void> => {
  try {
    if (preloadedConfig) {
      // Use preloaded config from consolidated endpoint
      githubConfig = preloadedConfig
    } else {
      // Fallback: fetch individual endpoint if needed
      githubConfig = await AuthService.getGitHubConfig()
    }
  } catch (error) {
    console.error("Failed to initialize GitHub config:", error)
    githubConfig = { enabled: false, client_id: null }
  }
}

export const getGithubLoginUrl = (
  redirectUri: string,
  state?: string,
): string => {
  const config = getGithubConfig()
  if (!config.client_id) {
    throw new Error("GitHub OAuth is not configured")
  }

  const params = new URLSearchParams({
    client_id: config.client_id,
    redirect_uri: redirectUri,
    scope: "user:email",
    state: state || Math.random().toString(36).substring(7),
  })

  return `https://github.com/login/oauth/authorize?${params.toString()}`
}
