import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation } from "@tanstack/react-query"
import {
  createFileRoute,
  Link as RouterLink,
  redirect,
  useNavigate,
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
import { LoadingButton } from "@/components/ui/loading-button"
import { PasswordInput } from "@/components/ui/password-input"
import { isLoggedIn } from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import i18n from "@/i18n/i18n"
import {
  type ResetPasswordFormData,
  resetPasswordFormSchema,
  resetPasswordSearchSchema,
} from "@/schemas/auth"
import { AuthService } from "@/services"

export const Route = createFileRoute("/reset-password")({
  component: ResetPassword,
  validateSearch: resetPasswordSearchSchema,
  beforeLoad: async ({ search }) => {
    if (isLoggedIn()) {
      throw redirect({ to: "/" })
    }
    if (!search.token) {
      throw redirect({ to: "/login" })
    }
  },
  head: () => ({
    meta: [
      {
        title: `${i18n.t("auth.resetPassword.metaTitle")} - Techletes`,
      },
    ],
  }),
})

function ResetPassword() {
  const { token } = Route.useSearch()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const navigate = useNavigate()
  const { t } = useTranslation()

  const form = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordFormSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      new_password: "",
      confirm_password: "",
    },
  })

  const mutation = useMutation({
    mutationFn: (data: { new_password: string; token: string }) =>
      AuthService.resetPassword(data),
    onSuccess: () => {
      showSuccessToast(t("auth.resetPassword.success"))
      form.reset()
      navigate({ to: "/login" })
    },
    onError: (error: Error) => showErrorToast(error.message),
  })

  const onSubmit = (data: ResetPasswordFormData) => {
    mutation.mutate({ new_password: data.new_password, token })
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
              {t("auth.resetPassword.title")}
            </h1>
            <p className="text-sm text-muted-foreground">
              {t("auth.resetPassword.subtitle")}
            </p>
          </div>

          <div className="grid gap-4">
            <FormField
              control={form.control}
              name="new_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("common.fields.newPassword")}</FormLabel>
                  <FormControl>
                    <PasswordInput
                      data-testid="new-password-input"
                      placeholder={t("common.placeholders.newPassword")}
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
              loading={mutation.isPending}
            >
              {t("auth.resetPassword.submit")}
            </LoadingButton>
          </div>

          <div className="text-center text-sm">
            {t("auth.recoverPassword.rememberPassword")}{" "}
            <RouterLink to="/login" className="underline underline-offset-4">
              {t("auth.recoverPassword.logIn")}
            </RouterLink>
          </div>
        </form>
      </Form>
    </AuthLayout>
  )
}
