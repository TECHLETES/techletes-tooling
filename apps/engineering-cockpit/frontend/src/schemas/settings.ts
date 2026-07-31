import { z } from "zod"

import i18n from "@/i18n/i18n"

export const changePasswordFormSchema = z
  .object({
    current_password: z
      .string()
      .min(1, { message: i18n.t("validation.passwordRequired") })
      .min(8, { message: i18n.t("validation.passwordMin") }),
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

export type ChangePasswordFormData = z.infer<typeof changePasswordFormSchema>

export const userInformationFormSchema = z.object({
  full_name: z.string().max(30).optional(),
  email: z.email({ message: i18n.t("validation.invalidEmail") }),
})

export type UserInformationFormData = z.infer<typeof userInformationFormSchema>
