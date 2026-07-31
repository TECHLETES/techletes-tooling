import { zodResolver } from "@hookform/resolvers/zod"
import { Pencil } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { useTranslation } from "react-i18next"
import type { ItemPublic, ItemUpdate } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { DropdownMenuItem } from "@/components/ui/dropdown-menu"
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
import { useItems } from "@/hooks/useItems"
import usePermissions from "@/hooks/usePermissions"
import { type EditItemFormData, editItemFormSchema } from "@/schemas/items"

interface EditItemProps {
  item: ItemPublic
  onSuccess: () => void
}

const EditItem = ({ item, onSuccess }: EditItemProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const { can } = usePermissions()
  const { updateItem, isUpdating } = useItems()
  const { t } = useTranslation()

  const form = useForm<EditItemFormData>({
    resolver: zodResolver(editItemFormSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      title: item.title,
      description: item.description ?? undefined,
    },
  })

  const onSubmit = async (data: EditItemFormData) => {
    try {
      await updateItem(item.id, data as ItemUpdate)
      setIsOpen(false)
      onSuccess()
    } catch {
      // Error toast is handled by the hook
    }
  }

  // Check if user has permission to edit items
  if (!can("items:update")) {
    return null
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuItem
        onSelect={(e) => e.preventDefault()}
        onClick={() => setIsOpen(true)}
      >
        <Pencil />
        {t("items.form.editTrigger")}
      </DropdownMenuItem>
      <DialogContent className="sm:max-w-md">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <DialogHeader>
              <DialogTitle>{t("items.form.editTitle")}</DialogTitle>
              <DialogDescription>
                {t("items.form.editDescription")}
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <FormField
                control={form.control}
                name="title"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      {t("common.fields.title")}{" "}
                      <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        placeholder={t("common.placeholders.title")}
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
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("common.fields.description")}</FormLabel>
                    <FormControl>
                      <Input
                        placeholder={t("common.placeholders.description")}
                        type="text"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline" disabled={isUpdating}>
                  {t("common.actions.cancel")}
                </Button>
              </DialogClose>
              <LoadingButton type="submit" loading={isUpdating}>
                {t("common.actions.save")}
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default EditItem
