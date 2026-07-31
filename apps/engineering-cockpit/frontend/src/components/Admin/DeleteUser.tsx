import { Trash2 } from "lucide-react"
import { useState } from "react"
import { useTranslation } from "react-i18next"
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
import { LoadingButton } from "@/components/ui/loading-button"
import { useUsers } from "@/hooks/useUsers"

interface DeleteUserProps {
  id: string
  onSuccess: () => void
}

const DeleteUser = ({ id, onSuccess }: DeleteUserProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const { deleteUser, isDeleting } = useUsers()
  const { t } = useTranslation()

  const onSubmit = async () => {
    try {
      await deleteUser(id)
      setIsOpen(false)
      onSuccess()
    } catch {
      // Error toast is handled by the hook
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuItem
        variant="destructive"
        onSelect={(e) => e.preventDefault()}
        onClick={() => setIsOpen(true)}
      >
        <Trash2 />
        {t("admin.users.delete.trigger")}
      </DropdownMenuItem>
      <DialogContent className="sm:max-w-md">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            onSubmit()
          }}
        >
          <DialogHeader>
            <DialogTitle>{t("admin.users.delete.title")}</DialogTitle>
            <DialogDescription>
              {t("admin.users.delete.description")}
            </DialogDescription>
          </DialogHeader>

          <DialogFooter className="mt-4">
            <DialogClose asChild>
              <Button variant="outline" disabled={isDeleting}>
                {t("common.actions.cancel")}
              </Button>
            </DialogClose>
            <LoadingButton
              variant="destructive"
              type="submit"
              loading={isDeleting}
            >
              {t("common.actions.delete")}
            </LoadingButton>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default DeleteUser
