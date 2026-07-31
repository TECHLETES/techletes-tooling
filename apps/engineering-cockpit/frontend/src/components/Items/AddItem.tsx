import { zodResolver } from "@hookform/resolvers/zod"
import { Plus } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { useTranslation } from "react-i18next"
import type { ItemCreate } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
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
import { type AddItemFormData, addItemFormSchema } from "@/schemas/items"

const AddItem = () => {
  const [isOpen, setIsOpen] = useState(false)
  const { can } = usePermissions()
  const { createItem, isCreating } = useItems()
  const { t } = useTranslation()

  const form = useForm<AddItemFormData>({
    resolver: zodResolver(addItemFormSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      title: "",
      description: "",
    },
  })

  const onSubmit = async (data: AddItemFormData) => {
    try {
      await createItem(data as ItemCreate)
      form.reset()
      setIsOpen(false)
    } catch {
      // Error toast is handled by the hook
    }
  }

  // Check if user has permission to create items
  if (!can("items:create")) {
    return null
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button className="my-4">
          <Plus className="mr-2" />
          {t("items.form.addTrigger")}
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{t("items.form.addTitle")}</DialogTitle>
          <DialogDescription>
            {t("items.form.addDescription")}
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
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
                        required
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
                <Button variant="outline" disabled={isCreating}>
                  {t("common.actions.cancel")}
                </Button>
              </DialogClose>
              <LoadingButton type="submit" loading={isCreating}>
                {t("common.actions.save")}
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default AddItem
