import { useState } from "react"
import { useTranslation } from "react-i18next"
import { getGithubLoginUrl, isGithubEnabled } from "@/auth/github"
import { GitHubIcon } from "@/components/ui/github-icon"
import { LoadingButton } from "@/components/ui/loading-button"

interface GitHubLoginButtonProps {
  onError?: (error: Error) => void
}

export function GitHubLoginButton({ onError }: GitHubLoginButtonProps) {
  const [isLoading, setIsLoading] = useState(false)
  const { t } = useTranslation()

  if (!isGithubEnabled()) return null

  const handleGithubLogin = () => {
    setIsLoading(true)

    try {
      // Get the redirect URI (current page after OAuth callback is handled)
      const redirectUri = `${window.location.origin}/auth/github/callback`
      const state = Math.random().toString(36).substring(7)

      // Store state in sessionStorage to verify callback
      sessionStorage.setItem("github_oauth_state", state)

      // Get login URL and redirect
      const loginUrl = getGithubLoginUrl(redirectUri, state)
      window.location.href = loginUrl
    } catch (error) {
      setIsLoading(false)
      onError?.(error as Error)
    }
  }

  return (
    <LoadingButton
      type="button"
      variant="outline"
      className="w-full"
      onClick={handleGithubLogin}
      loading={isLoading}
      data-testid="github-login-button"
    >
      <GitHubIcon className="mr-2 h-4 w-4" />
      {t("auth.social.github")}
    </LoadingButton>
  )
}
