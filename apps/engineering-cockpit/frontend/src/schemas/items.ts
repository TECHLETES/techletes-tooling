import { z } from "zod"

import i18n from "@/i18n/i18n"

export const addItemFormSchema = z.object({
  title: z.string().min(1, { message: i18n.t("validation.titleRequired") }),
  description: z.string().optional(),
})

export type AddItemFormData = z.infer<typeof addItemFormSchema>

export const editItemFormSchema = z.object({
  title: z.string().min(1, { message: i18n.t("validation.titleRequired") }),
  description: z.string().optional(),
})

export type EditItemFormData = z.infer<typeof editItemFormSchema>
