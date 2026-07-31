import { useMsal } from "@azure/msal-react"
import { useState } from "react"
import { useTranslation } from "react-i18next"
import { isEntraEnabled, loginScopes } from "@/auth/entra"
import { LoadingButton } from "@/components/ui/loading-button"

interface EntraLoginButtonProps {
  onSuccess: (idToken: string) => void
  onError?: (error: Error) => void
}

export function EntraLoginButton({
  onSuccess,
  onError,
}: EntraLoginButtonProps) {
  const { instance } = useMsal()
  const [isLoading, setIsLoading] = useState(false)
  const { t } = useTranslation()

  if (!isEntraEnabled()) return null

  const handleLogin = async () => {
    setIsLoading(true)
    try {
      const response = await instance.loginPopup({
        scopes: loginScopes,
      })

      if (response.idToken) {
        onSuccess(response.idToken)
      }
    } catch (error) {
      onError?.(error as Error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <LoadingButton
      type="button"
      variant="outline"
      className="w-full"
      onClick={handleLogin}
      loading={isLoading}
      data-testid="entra-login-button"
    >
      <svg
        className="mr-2 h-4 w-4"
        viewBox="0 0 21 21"
        fill="none"
        aria-hidden="true"
      >
        <rect x="1" y="1" width="9" height="9" fill="#f25022" />
        <rect x="11" y="1" width="9" height="9" fill="#7fba00" />
        <rect x="1" y="11" width="9" height="9" fill="#00a4ef" />
        <rect x="11" y="11" width="9" height="9" fill="#ffb900" />
      </svg>
      {t("auth.social.microsoft")}
    </LoadingButton>
  )
}
