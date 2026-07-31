import { zodResolver } from "@hookform/resolvers/zod"
import {
  createFileRoute,
  Link as RouterLink,
  redirect,
} from "@tanstack/react-router"
import { useForm } from "react-hook-form"
import { useTranslation } from "react-i18next"
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
import useAppConfig from "@/hooks/useAppConfig"
import useAuth, { isLoggedIn } from "@/hooks/useAuth"
import i18n from "@/i18n/i18n"
import { type SignUpFormData, signUpFormSchema } from "@/schemas/auth"

export const Route = createFileRoute("/signup")({
  component: SignUp,
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
        title: `${i18n.t("auth.signup.metaTitle")} - Techletes`,
      },
    ],
  }),
})

function SignUp() {
  const { signUpMutation } = useAuth()
  const { config, isLoading, error } = useAppConfig()
  const { t } = useTranslation()
  const form = useForm<SignUpFormData>({
    resolver: zodResolver(signUpFormSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      email: "",
      full_name: "",
      password: "",
      confirm_password: "",
    },
  })

  if (isLoading) {
    return (
      <AuthLayout>
        <div className="text-center">
          <p>{t("common.status.loading")}</p>
        </div>
      </AuthLayout>
    )
  }

  if (error || !config?.signup_enabled) {
    return (
      <AuthLayout>
        <div className="flex flex-col gap-6">
          <div className="flex flex-col items-center gap-2 text-center">
            <h1 className="text-2xl font-bold">
              {t("auth.signup.unavailableTitle")}
            </h1>
          </div>
          <p className="text-center text-sm text-muted-foreground">
            {t("auth.signup.unavailableDescription")}
          </p>
          <RouterLink
            to="/login"
            className="text-center underline underline-offset-4"
          >
            {t("auth.signup.backToLogin")}
          </RouterLink>
        </div>
      </AuthLayout>
    )
  }

  const onSubmit = (data: SignUpFormData) => {
    if (signUpMutation.isPending) return

    // exclude confirm_password from submission data
    const { confirm_password: _confirm_password, ...submitData } = data
    signUpMutation.mutate(submitData)
  }

  return (
    <AuthLayout>
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="flex flex-col gap-6"
        >
          <div className="flex flex-col items-center gap-2 text-center mb-6">
            <h1 className="text-2xl font-semibold tracking-tight">
              {t("auth.signup.title")}
            </h1>
            <p className="text-sm text-muted-foreground">
              {t("auth.signup.subtitle")}
            </p>
          </div>

          <div className="grid gap-4">
            <FormField
              control={form.control}
              name="full_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("common.fields.fullName")}</FormLabel>
                  <FormControl>
                    <Input
                      data-testid="full-name-input"
                      placeholder={t("common.placeholders.fullName")}
                      type="text"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="email"
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
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("common.fields.password")}</FormLabel>
                  <FormControl>
                    <PasswordInput
                      data-testid="password-input"
                      placeholder={t("common.placeholders.password")}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="confirm_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("common.fields.confirmPassword")}</FormLabel>
                  <FormControl>
                    <PasswordInput
                      data-testid="confirm-password-input"
                      placeholder={t("common.placeholders.confirmPassword")}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <LoadingButton
              type="submit"
              className="w-full"
              loading={signUpMutation.isPending}
            >
              {t("auth.signup.submit")}
            </LoadingButton>
          </div>

          <div className="text-center text-sm">
            {t("auth.signup.haveAccount")}{" "}
            <RouterLink to="/login" className="underline underline-offset-4">
              {t("auth.signup.logIn")}
            </RouterLink>
          </div>
        </form>
      </Form>
    </AuthLayout>
  )
}
