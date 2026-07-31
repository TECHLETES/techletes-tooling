import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation } from "@tanstack/react-query"
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
import { isLoggedIn } from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import i18n from "@/i18n/i18n"
import {
  type RecoverPasswordFormData,
  recoverPasswordFormSchema,
} from "@/schemas/auth"
import { AuthService } from "@/services"

export const Route = createFileRoute("/recover-password")({
  component: RecoverPassword,
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
        title: `${i18n.t("auth.recoverPassword.metaTitle")} - Techletes`,
      },
    ],
  }),
})

function RecoverPassword() {
  const { t } = useTranslation()
  const form = useForm<RecoverPasswordFormData>({
    resolver: zodResolver(recoverPasswordFormSchema),
    defaultValues: {
      email: "",
    },
  })
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const recoverPassword = async (data: RecoverPasswordFormData) => {
    await AuthService.recoverPassword(data.email)
  }

  const mutation = useMutation({
    mutationFn: recoverPassword,
    onSuccess: () => {
      showSuccessToast(t("auth.recoverPassword.success"))
      form.reset()
    },
    onError: (error: Error) => showErrorToast(error.message),
  })

  const onSubmit = async (data: RecoverPasswordFormData) => {
    if (mutation.isPending) return
    mutation.mutate(data)
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
              {t("auth.recoverPassword.title")}
            </h1>
            <p className="text-sm text-muted-foreground">
              {t("auth.recoverPassword.subtitle")}
            </p>
          </div>

          <div className="grid gap-4">
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

            <LoadingButton
              type="submit"
              className="w-full"
              loading={mutation.isPending}
            >
              {t("common.actions.continue")}
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
