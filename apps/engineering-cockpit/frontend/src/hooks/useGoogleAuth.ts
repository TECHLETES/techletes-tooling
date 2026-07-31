import { useMutation } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"

import type { Token } from "@/client"
import { AuthService } from "@/services"
import useCustomToast from "./useCustomToast"

interface GoogleLoginData {
  code: string
}

async function googleLogin(data: GoogleLoginData): Promise<Token> {
  return AuthService.exchangeGoogleCode(data)
}

const useGoogleAuth = () => {
  const navigate = useNavigate()
  const { showErrorToast } = useCustomToast()

  const googleLoginMutation = useMutation({
    mutationFn: googleLogin,
    onSuccess: () => {
      navigate({ to: "/" })
    },
    onError: (error: Error) => {
      showErrorToast(error.message)
    },
  })

  return { googleLoginMutation }
}

export default useGoogleAuth
