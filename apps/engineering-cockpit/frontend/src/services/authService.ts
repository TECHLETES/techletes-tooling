/**
 * Auth Service
 * Business logic wrapper around auth-related API client endpoints.
 */

import {
  type Body_login_login_access_token as AccessToken,
  AuthConfigService,
  AuthEntraService,
  AuthGithubService,
  AuthGoogleService,
  type ConsolidatedAuthConfig,
  client,
  type EntraLoginRequest,
  type GitHubExchangeCodeRequest,
  type GitHubLoginRequest,
  type GitHubProviderConfig,
  type GoogleLoginRequest,
  type GoogleProviderConfig,
  LoginService,
  type Message,
  type NewPassword,
  type Token,
} from "@/client"

export const AuthService = {
  async getConsolidatedConfig(): Promise<ConsolidatedAuthConfig> {
    return AuthConfigService.getApiV1AuthConfig()
  },

  async getGitHubConfig(): Promise<GitHubProviderConfig> {
    return AuthGithubService.getApiV1AuthGithubConfig()
  },

  async getGoogleConfig(): Promise<GoogleProviderConfig> {
    return AuthGoogleService.getApiV1AuthGoogleConfig()
  },

  async getEntraConfig() {
    return AuthEntraService.getApiV1AuthEntraConfig()
  },

  async loginWithGitHubToken(data: GitHubLoginRequest): Promise<Token> {
    return AuthGithubService.postApiV1AuthGithubLogin({ body: data })
  },

  async loginWithAccessToken(
    data: {
      username: string
      password: string
      grant_type?: string | null
      scope?: string | null
      client_id?: string | null
      client_secret?: string | null
    } & AccessToken,
  ): Promise<Token> {
    return LoginService.loginAccessToken({ formData: data })
  },

  async loginWithGoogleToken(data: GoogleLoginRequest): Promise<Token> {
    return AuthGoogleService.postApiV1AuthGoogleLogin({ body: data })
  },

  async exchangeGoogleCode(data: { code: string }): Promise<Token> {
    const response = await client.post({
      url: "/api/v1/auth/google/exchange-code",
      body: data,
    })
    return response.data as Token
  },

  async loginWithEntraToken(data: EntraLoginRequest): Promise<Token> {
    return AuthEntraService.postApiV1AuthEntraLogin({ body: data })
  },

  async logout(): Promise<Message> {
    const response = await client.post({
      url: "/api/v1/login/logout",
    })
    return response.data as Message
  },

  async exchangeGitHubCode(data: GitHubExchangeCodeRequest): Promise<Token> {
    return AuthGithubService.postApiV1AuthGithubExchangeCode({ body: data })
  },

  async recoverPassword(email: string): Promise<Message> {
    return LoginService.recoverPassword({ email })
  },

  async resetPassword(requestBody: NewPassword): Promise<Message> {
    return LoginService.resetPassword({ requestBody })
  },
}
