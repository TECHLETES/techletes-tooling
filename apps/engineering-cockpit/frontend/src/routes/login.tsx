import { zodResolver } from "@hookform/resolvers/zod"
import {
  createFileRoute,
  Link as RouterLink,
  redirect,
} from "@tanstack/react-router"
import { useForm } from "react-hook-form"
import { useTranslation } from "react-i18next"
import { isEntraEnabled } from "@/auth/entra"
import { isGithubEnabled } from "@/auth/github"
import { isGoogleEnabled } from "@/auth/google"
import { EntraLoginButton } from "@/components/Auth/EntraLogin"
import { GitHubLoginButton } from "@/components/Auth/GitHubLogin"
import { GoogleLoginButton } from "@/components/Auth/GoogleLogin"
import { AuthLayout } from "@/components/Common/AuthLayout"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import { PasswordInput } from "@/components/ui/password-input"
import { Separator } from "@/components/ui/separator"
import useAppConfig from "@/hooks/useAppConfig"
import useAuth, { isLoggedIn } from "@/hooks/useAuth"
import useEntraAuth from "@/hooks/useEntraAuth"
import useGoogleAuth from "@/hooks/useGoogleAuth"
import i18n from "@/i18n/i18n"
import { type LoginFormData, loginFormSchema } from "@/schemas/auth"

export const Route = createFileRoute("/login")({
  component: Login,
  beforeLoad: async () => {
    if (isLoggedIn()) {
      throw redirect({
        to: "/",
      })
    }
  },
  head: () => ({
    meta: [
      {
        title: `${i18n.t("auth.login.metaTitle")} - Techletes`,
      },
    ],
  }),
})

function Login() {
  const { loginMutation } = useAuth()
  const { entraLoginMutation } = useEntraAuth()
  const { googleLoginMutation } = useGoogleAuth()
  const { config } = useAppConfig()
  const { t } = useTranslation()
  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginFormSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      username: "",
      password: "",
    },
  })

  const onSubmit = (data: LoginFormData) => {
    if (loginMutation.isPending) return
    loginMutation.mutate(data)
  }

  const handleEntraLogin = (idToken: string) => {
    entraLoginMutation.mutate({ id_token: idToken })
  }

  const handleGoogleLogin = (code: string) => {
    googleLoginMutation.mutate({ code })
  }

  const showOAuthSeparator =
    isEntraEnabled() || isGoogleEnabled() || isGithubEnabled()

  return (
    <AuthLayout>
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="flex flex-col gap-6"
        >
          <div className="flex flex-col items-center gap-2 text-center mb-6">
            <h1 className="text-2xl font-semibold tracking-tight">
              {t("auth.login.title")}
            </h1>
            <p className="text-sm text-muted-foreground">
              {t("auth.login.subtitle")}
            </p>
          </div>
          <div className="flex flex-col gap-2">
            {isEntraEnabled() && (
              <EntraLoginButton
                onSuccess={handleEntraLogin}
                onError={(error) => console.error("Entra login failed:", error)}
              />
            )}

            {isGoogleEnabled() && (
              <GoogleLoginButton
                onSuccess={handleGoogleLogin}
                onError={(error) =>
                  console.error("Google login failed:", error)
                }
              />
            )}

            {isGithubEnabled() && (
              <GitHubLoginButton
                onError={(error) =>
                  console.error("GitHub login failed:", error)
                }
              />
            )}
          </div>

          {showOAuthSeparator && (
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <Separator className="w-full" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">
                  {t("auth.login.orContinueWith")}
                </span>
              </div>
            </div>
          )}

          <div className="grid gap-4">
            <FormField
              control={form.control}
              name="username"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("common.fields.email")}</FormLabel>
                  <FormControl>
                    <Input
                      data-testid="email-input"
                      placeholder={t("common.placeholders.email")}
                      type="email"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage className="text-xs" />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <div className="flex items-center">
                    <FormLabel>{t("common.fields.password")}</FormLabel>
                    <RouterLink
                      to="/recover-password"
                      className="ml-auto text-sm underline-offset-4 hover:underline"
                    >
                      {t("auth.login.forgotPassword")}
                    </RouterLink>
                  </div>
                  <FormControl>
                    <PasswordInput
                      data-testid="password-input"
                      placeholder={t("common.placeholders.password")}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage className="text-xs" />
                </FormItem>
              )}
            />

            <LoadingButton type="submit" loading={loginMutation.isPending}>
              {t("auth.login.submit")}
            </LoadingButton>
          </div>

          {config?.signup_enabled && (
            <div className="text-center text-sm">
              {t("auth.login.noAccount")}{" "}
              <RouterLink to="/signup" className="underline underline-offset-4">
                {t("auth.login.signUp")}
              </RouterLink>
            </div>
          )}
        </form>
      </Form>
    </AuthLayout>
  )
}
