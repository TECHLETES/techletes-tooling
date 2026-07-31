import { useMutation, useQuery } from "@tanstack/react-query"
import { X } from "lucide-react"
import { useState } from "react"
import { useTranslation } from "react-i18next"
import { isEntraEnabled } from "@/auth/entra"
import type { UserPublic } from "@/client"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { DropdownMenuItem } from "@/components/ui/dropdown-menu"
import { LoadingButton } from "@/components/ui/loading-button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import useCustomToast from "@/hooks/useCustomToast"
import { RolesService } from "@/services"

/**
 * Props for UserRoleAssigner component
 */
interface UserRoleAssignerProps {
  /** User to assign roles to */
  user: UserPublic
  /** Callback when roles are updated */
  onRolesUpdated: () => void
}

/**
 * Component for assigning and removing roles from a user.
 * Displays current roles with remove buttons and allows adding new roles.
 */
export const UserRoleAssigner = ({
  user,
  onRolesUpdated,
}: UserRoleAssignerProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const [selectedRoleId, setSelectedRoleId] = useState<string>("")
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const entraEnabled = isEntraEnabled()
  const { t } = useTranslation()

  // Fetch user's current roles
  const {
    data: userRoles,
    isLoading: rolesLoading,
    refetch: refetchRoles,
  } = useQuery({
    queryKey: ["user", user.id, "roles"],
    queryFn: () => RolesService.getUserRoles(user.id),
    enabled: isOpen,
  })

  // Fetch all available roles
  const { data: allRolesData, isLoading: allRolesLoading } = useQuery({
    queryKey: ["roles"],
    queryFn: () => RolesService.listRoles(0, 1000),
    enabled: isOpen,
  })

  // Calculate available roles (not already assigned)
  const availableRoles =
    allRolesData?.roles?.filter(
      (role) => !userRoles?.some((userRole) => userRole.id === role.id),
    ) || []

  // Mutation to assign role
  const assignMutation = useMutation({
    mutationFn: (roleId: string) =>
      RolesService.assignRoleToUser(user.id, roleId),
    onSuccess: () => {
      showSuccessToast(t("roles.feedback.assigned"))
      setSelectedRoleId("")
      refetchRoles()
    },
    onError: (error: Error) => showErrorToast(error.message),
  })

  // Mutation to remove role
  const removeMutation = useMutation({
    mutationFn: (roleId: string) =>
      RolesService.removeRoleFromUser(user.id, roleId),
    onSuccess: () => {
      showSuccessToast(t("roles.feedback.removed"))
      refetchRoles()
    },
    onError: (error: Error) => showErrorToast(error.message),
  })

  /**
   * Handle assigning a role
   */
  const handleAssignRole = () => {
    if (selectedRoleId) {
      assignMutation.mutate(selectedRoleId)
    }
  }

  /**
   * Handle removing a role
   */
  const handleRemoveRole = (roleId: string) => {
    removeMutation.mutate(roleId)
  }

  /**
   * Handle dialog close
   */
  const handleClose = (open: boolean) => {
    setIsOpen(open)
    if (!open) {
      setSelectedRoleId("")
      onRolesUpdated()
    }
  }

  const isLoading =
    rolesLoading ||
    allRolesLoading ||
    assignMutation.isPending ||
    removeMutation.isPending

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DropdownMenuItem
        onSelect={(e) => e.preventDefault()}
        onClick={() => setIsOpen(true)}
      >
        {t("admin.userRoles.trigger")}
      </DropdownMenuItem>

      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{t("admin.userRoles.title")}</DialogTitle>
          <DialogDescription>
            {t("admin.userRoles.description", { email: user.email })}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {entraEnabled && (
            <Alert>
              <AlertTitle>{t("admin.userRoles.entraTitle")}</AlertTitle>
              <AlertDescription>
                {t("admin.userRoles.entraDescription")}
              </AlertDescription>
            </Alert>
          )}

          {/* User Information */}
          <div className="space-y-2">
            <p className="text-sm font-medium">
              {t("admin.userRoles.userInformation")}
            </p>
            <div className="space-y-1 text-sm">
              <div>
                <span className="text-muted-foreground">
                  {t("common.fields.email")}:
                </span>{" "}
                {user.email}
              </div>
              {user.full_name && (
                <div>
                  <span className="text-muted-foreground">
                    {t("common.fields.name")}:
                  </span>{" "}
                  {user.full_name}
                </div>
              )}
            </div>
          </div>

          {/* Current Roles */}
          <div className="space-y-2">
            <p className="text-sm font-medium">
              {t("admin.userRoles.currentRoles")}
            </p>
            <div className="min-h-12 p-3 border rounded-md bg-muted/50">
              {rolesLoading ? (
                <p className="text-sm text-muted-foreground">
                  {t("admin.userRoles.loadingRoles")}
                </p>
              ) : userRoles?.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  {t("admin.userRoles.noRoles")}
                </p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {userRoles?.map((role) => (
                    <Badge key={role.id} variant="secondary" className="group">
                      {role.name}
                      <button
                        type="button"
                        onClick={() => handleRemoveRole(role.id)}
                        disabled={removeMutation.isPending}
                        className="ml-1 hover:opacity-70 disabled:opacity-50"
                        aria-label={t("admin.userRoles.removeRole", {
                          name: role.name,
                        })}
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Assign New Role */}
          {availableRoles.length > 0 && (
            <div className="space-y-3">
              <p className="text-sm font-medium">
                {t("admin.userRoles.assignNewRole")}
              </p>
              <div className="flex gap-2">
                <Select
                  value={selectedRoleId}
                  onValueChange={setSelectedRoleId}
                >
                  <SelectTrigger disabled={isLoading}>
                    <SelectValue
                      placeholder={t("admin.userRoles.selectRole")}
                    />
                  </SelectTrigger>
                  <SelectContent>
                    {availableRoles.map((role) => (
                      <SelectItem key={role.id} value={role.id}>
                        {role.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <LoadingButton
                  size="sm"
                  onClick={handleAssignRole}
                  disabled={!selectedRoleId}
                  loading={assignMutation.isPending}
                >
                  {t("admin.userRoles.addRole")}
                </LoadingButton>
              </div>
            </div>
          )}

          {availableRoles.length === 0 && (userRoles?.length || 0) > 0 && (
            <p className="text-sm text-muted-foreground">
              {t("admin.userRoles.allRolesAssigned")}
            </p>
          )}
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => handleClose(false)}
            disabled={isLoading}
          >
            {t("common.actions.done")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default UserRoleAssigner
