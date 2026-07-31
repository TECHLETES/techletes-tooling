import { useMutation } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"

import type { Token } from "@/client"
import { AuthService } from "@/services"
import useCustomToast from "./useCustomToast"

interface EntraLoginData {
  id_token: string
}

async function entraLogin(data: EntraLoginData): Promise<Token> {
  return AuthService.loginWithEntraToken(data)
}

const useEntraAuth = () => {
  const navigate = useNavigate()
  const { showErrorToast } = useCustomToast()

  const entraLoginMutation = useMutation({
    mutationFn: entraLogin,
    onSuccess: () => {
      navigate({ to: "/" })
    },
    onError: (error: Error) => {
      showErrorToast(error.message)
    },
  })

  return { entraLoginMutation }
}

export default useEntraAuth
