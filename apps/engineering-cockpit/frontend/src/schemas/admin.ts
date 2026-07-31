import { z } from "zod"

import i18n from "@/i18n/i18n"

export const addUserFormSchema = z
  .object({
    email: z.email({ message: i18n.t("validation.invalidEmail") }),
    full_name: z.string().optional(),
    password: z
      .string()
      .min(1, { message: i18n.t("validation.passwordRequired") })
      .min(8, { message: i18n.t("validation.passwordMin") }),
    confirm_password: z
      .string()
      .min(1, { message: i18n.t("validation.passwordConfirmationRequired") }),
    is_superuser: z.boolean(),
    is_active: z.boolean(),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: i18n.t("validation.passwordsDoNotMatch"),
    path: ["confirm_password"],
  })

export type AddUserFormData = z.infer<typeof addUserFormSchema>

export const editUserFormSchema = z
  .object({
    email: z.email({ message: i18n.t("validation.invalidEmail") }),
    full_name: z.string().optional(),
    password: z
      .string()
      .min(8, { message: i18n.t("validation.passwordMin") })
      .optional()
      .or(z.literal("")),
    confirm_password: z.string().optional(),
    is_superuser: z.boolean().optional(),
    is_active: z.boolean().optional(),
  })
  .refine((data) => !data.password || data.password === data.confirm_password, {
    message: i18n.t("validation.passwordsDoNotMatch"),
    path: ["confirm_password"],
  })

export type EditUserFormData = z.infer<typeof editUserFormSchema>

export const roleFormSchema = z.object({
  name: z
    .string()
    .min(2, { message: i18n.t("validation.roleNameMin") })
    .max(255, { message: i18n.t("validation.roleNameMax") })
    .regex(/^[a-z0-9_]+$/, {
      message: i18n.t("validation.roleNamePattern"),
    }),
  description: z
    .string()
    .max(500, { message: i18n.t("validation.descriptionMax") })
    .optional()
    .nullable(),
  permission_ids: z.array(z.string()),
  entra_role_id: z
    .string()
    .max(255, { message: i18n.t("validation.entraRoleIdMax") })
    .optional()
    .nullable(),
})

export type RoleFormData = z.infer<typeof roleFormSchema>
