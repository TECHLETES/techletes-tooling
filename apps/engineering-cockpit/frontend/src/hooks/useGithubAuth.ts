import { useMutation } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"

import type { Token } from "@/client"
import { AuthService } from "@/services"
import useCustomToast from "./useCustomToast"

interface GitHubLoginData {
  access_token: string
}

async function githubLogin(data: GitHubLoginData): Promise<Token> {
  return AuthService.loginWithGitHubToken(data)
}

const useGithubAuth = () => {
  const navigate = useNavigate()
  const { showErrorToast } = useCustomToast()

  const githubLoginMutation = useMutation({
    mutationFn: githubLogin,
    onSuccess: () => {
      navigate({ to: "/" })
    },
    onError: (error: Error) => {
      showErrorToast(error.message)
    },
  })

  return { githubLoginMutation }
}

export default useGithubAuth
