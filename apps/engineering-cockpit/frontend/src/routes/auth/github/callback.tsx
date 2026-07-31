import { createFileRoute, useNavigate, useSearch } from "@tanstack/react-router"
import { Loader2 } from "lucide-react"
import { useEffect, useState } from "react"
import { useTranslation } from "react-i18next"
import useCustomToast from "@/hooks/useCustomToast"
import { AuthService } from "@/services"

export const Route = createFileRoute("/auth/github/callback")({
  validateSearch: (search: Record<string, unknown>) => ({
    code: (search.code as string) || "",
    state: (search.state as string) || "",
  }),
  component: RouteComponent,
})

function RouteComponent() {
  const navigate = useNavigate()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [isProcessing, setIsProcessing] = useState(true)
  const { code, state } = useSearch({ from: "/auth/github/callback" })
  const { t } = useTranslation()

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Validate state parameter (CSRF protection)
        const storedState = sessionStorage.getItem("github_oauth_state")
        if (state !== storedState) {
          throw new Error(t("auth.githubCallback.errors.stateMismatch"))
        }

        if (!code) {
          throw new Error(t("auth.githubCallback.errors.noCode"))
        }

        // Exchange code for token
        const data = await AuthService.exchangeGitHubCode({ code })

        if (!data.access_token) {
          throw new Error(t("auth.githubCallback.errors.noAccessToken"))
        }

        // Clear state from session storage
        sessionStorage.removeItem("github_oauth_state")

        // Show success message
        showSuccessToast(t("auth.githubCallback.success"))

        // Redirect to home page
        navigate({ to: "/" })
      } catch (error) {
        console.error("GitHub callback error:", error)

        // Show error message
        const errorMessage =
          error instanceof Error
            ? error.message
            : t("auth.githubCallback.errors.generic")

        showErrorToast(errorMessage)

        // Redirect to login after a brief delay
        setTimeout(() => {
          navigate({ to: "/login" })
        }, 2000)
      } finally {
        setIsProcessing(false)
      }
    }

    handleCallback()
  }, [code, state, navigate, showSuccessToast, showErrorToast, t])

  if (isProcessing) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin" />
          <p className="text-sm text-muted-foreground">
            {t("auth.githubCallback.processing")}
          </p>
        </div>
      </div>
    )
  }

  return null
}
