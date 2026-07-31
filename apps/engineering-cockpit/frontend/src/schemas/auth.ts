import { z } from "zod"

import i18n from "@/i18n/i18n"

export const loginFormSchema = z.object({
  username: z.email(),
  password: z
    .string()
    .min(1, { message: i18n.t("validation.passwordRequired") })
    .min(8, { message: i18n.t("validation.passwordMin") }),
})

export type LoginFormData = z.infer<typeof loginFormSchema>

export const signUpFormSchema = z
  .object({
    email: z.email(),
    full_name: z
      .string()
      .min(1, { message: i18n.t("validation.fullNameRequired") }),
    password: z
      .string()
      .min(1, { message: i18n.t("validation.passwordRequired") })
      .min(8, { message: i18n.t("validation.passwordMin") }),
    confirm_password: z
      .string()
      .min(1, { message: i18n.t("validation.passwordConfirmationRequired") }),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: i18n.t("validation.passwordsDoNotMatch"),
    path: ["confirm_password"],
  })

export type SignUpFormData = z.infer<typeof signUpFormSchema>

export const recoverPasswordFormSchema = z.object({
  email: z.email(),
})

export type RecoverPasswordFormData = z.infer<typeof recoverPasswordFormSchema>

export const resetPasswordSearchSchema = z.object({
  token: z.string().catch(""),
})

export const resetPasswordFormSchema = z
  .object({
    new_password: z
      .string()
      .min(1, { message: i18n.t("validation.passwordRequired") })
      .min(8, { message: i18n.t("validation.passwordMin") }),
    confirm_password: z
      .string()
      .min(1, { message: i18n.t("validation.passwordConfirmationRequired") }),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: i18n.t("validation.passwordsDoNotMatch"),
    path: ["confirm_password"],
  })

export type ResetPasswordFormData = z.infer<typeof resetPasswordFormSchema>
