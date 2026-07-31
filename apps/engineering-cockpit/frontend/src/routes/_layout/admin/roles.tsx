import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Copy, FileJson, Plus, Trash2 } from "lucide-react"
import { useState } from "react"
import { useTranslation } from "react-i18next"
import { isEntraEnabled } from "@/auth/entra"
import { createRouteGuard } from "@/auth/roleGuard"
import type {
  EntraAppRoleManifestPublic,
  RoleCreate,
  RolePublic,
  RoleUpdate,
} from "@/client"
import RoleForm from "@/components/Admin/RoleForm"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useCopyToClipboard } from "@/hooks/useCopyToClipboard"
import useCustomToast from "@/hooks/useCustomToast"
import usePermissions from "@/hooks/usePermissions"
import i18n from "@/i18n/i18n"
import { RolesService } from "@/services"

type EntraAppRoleManifest = EntraAppRoleManifestPublic

async function fetchEntraManifest(): Promise<EntraAppRoleManifest> {
  return RolesService.getEntraManifest()
}

export const Route = createFileRoute("/_layout/admin/roles")({
  component: RolesPage,
  beforeLoad: createRouteGuard({
    requiredPermissions: ["rbac:view_roles"],
  }),
  head: () => ({
    meta: [
      {
        title: `${i18n.t("admin.roles.page.metaTitle")} - Techletes`,
      },
    ],
  }),
})

function RolesPage() {
  const queryClient = useQueryClient()
  const { can } = usePermissions()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const { t } = useTranslation()

  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [editingRole, setEditingRole] = useState<RolePublic | null>(null)
  const [deleteConfirming, setDeleteConfirming] = useState<RolePublic | null>(
    null,
  )
  const [viewingPermissions, setViewingPermissions] =
    useState<RolePublic | null>(null)
  const [isManifestOpen, setIsManifestOpen] = useState(false)
  const [copiedManifest, copyManifest] = useCopyToClipboard()
  const entraEnabled = isEntraEnabled()

  // Fetch all roles
  const {
    data: rolesData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["roles"],
    queryFn: () => RolesService.listRoles(0, 1000),
  })

  const {
    data: manifestData,
    isLoading: manifestLoading,
    error: manifestError,
  } = useQuery({
    queryKey: ["roles", "entra-manifest"],
    queryFn: fetchEntraManifest,
    enabled: isManifestOpen,
  })

  // Create/Update role mutation
  const saveRoleMutation = useMutation({
    mutationFn: async (data: RoleCreate | RoleUpdate) => {
      if (editingRole) {
        const updateData: RoleUpdate = {
          name: data.name ?? null,
          description: data.description ?? null,
          permission_ids: data.permission_ids ?? null,
          entra_role_id: data.entra_role_id ?? null,
        }
        return RolesService.updateRole(editingRole.id, updateData)
      }

      const createData: RoleCreate = {
        name: data.name ?? "",
        description: data.description ?? null,
        permission_ids: data.permission_ids ?? [],
        entra_role_id: data.entra_role_id ?? null,
      }

      return RolesService.createRole(createData)
    },
    onSuccess: (_data) => {
      showSuccessToast(
        editingRole ? t("roles.feedback.updated") : t("roles.feedback.created"),
      )
      queryClient.invalidateQueries({ queryKey: ["roles"] })
      setIsCreateOpen(false)
      setEditingRole(null)
    },
    onError: (error: Error) => showErrorToast(error.message),
  })

  // Delete role mutation
  const deleteRoleMutation = useMutation({
    mutationFn: (roleId: string) => RolesService.deleteRole(roleId),
    onSuccess: () => {
      showSuccessToast(t("roles.feedback.deleted"))
      queryClient.invalidateQueries({ queryKey: ["roles"] })
      setDeleteConfirming(null)
    },
    onError: (error: Error) => showErrorToast(error.message),
  })

  /**
   * Handle form submission for create/edit
   */
  const handleSaveRole = async (data: RoleCreate | RoleUpdate) => {
    saveRoleMutation.mutate(data)
  }

  /**
   * Handle delete role
   */
  const handleDeleteRole = (role: RolePublic) => {
    if (!role.is_system) {
      setDeleteConfirming(role)
    }
  }

  /**
   * Handle edit role
   */
  const handleEditRole = (role: RolePublic) => {
    setEditingRole(role)
    setIsCreateOpen(true)
  }

  /**
   * Handle closing create/edit dialog
   */
  const handleCloseCreateDialog = () => {
    setIsCreateOpen(false)
    setEditingRole(null)
  }

  const roles = rolesData?.roles || []
  const canCreateRole = can("rbac:create_role")
  const canDeleteRole = can("rbac:delete_role")
  const manifestJson = manifestData ? JSON.stringify(manifestData, null, 2) : ""

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{t("admin.roles.page.title")}</h1>
          <p className="text-muted-foreground mt-1">
            {t("admin.roles.page.subtitle")}
          </p>
        </div>
        <div className="flex gap-2">
          {entraEnabled && (
            <Button variant="outline" onClick={() => setIsManifestOpen(true)}>
              <FileJson className="mr-2 h-4 w-4" />
              {t("admin.roles.page.exportManifest")}
            </Button>
          )}
          {canCreateRole && (
            <Button
              onClick={() => {
                setEditingRole(null)
                setIsCreateOpen(true)
              }}
            >
              <Plus className="mr-2 h-4 w-4" />
              {t("common.actions.create")}
            </Button>
          )}
        </div>
      </div>

      {entraEnabled && (
        <Alert>
          <AlertTitle>{t("admin.roles.page.entraAlertTitle")}</AlertTitle>
          <AlertDescription>
            {t("admin.roles.page.entraAlertDescription")}
          </AlertDescription>
        </Alert>
      )}

      {/* Loading/Error states */}
      {isLoading && (
        <div className="flex justify-center py-8">
          <p className="text-muted-foreground">
            {t("admin.roles.page.loading")}
          </p>
        </div>
      )}

      {error && (
        <div className="rounded-md bg-destructive/10 p-4">
          <p className="text-sm font-medium text-destructive">
            Failed to load roles: {error.message}
          </p>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && roles.length === 0 && (
        <div className="rounded-md border border-dashed p-8 text-center">
          <p className="text-muted-foreground mb-4">
            {t("admin.roles.page.empty")}
          </p>
          {canCreateRole && (
            <Button
              onClick={() => {
                setEditingRole(null)
                setIsCreateOpen(true)
              }}
            >
              <Plus className="mr-2 h-4 w-4" />
              {t("admin.roles.page.createFirst")}
            </Button>
          )}
        </div>
      )}

      {/* Roles table */}
      {!isLoading && !error && roles.length > 0 && (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("common.fields.name")}</TableHead>
                <TableHead>{t("common.fields.description")}</TableHead>
                {entraEnabled && (
                  <TableHead>{t("common.fields.entraRoleId")}</TableHead>
                )}
                <TableHead>{t("common.fields.permissions")}</TableHead>
                <TableHead className="text-right">
                  {t("common.columns.actions")}
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {roles.map((role) => (
                <TableRow key={role.id}>
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-2">
                      {role.name}
                      {role.is_system && (
                        <Badge variant="outline" className="text-xs">
                          {t("admin.roles.page.systemBadge")}
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-muted-foreground text-sm">
                    {role.description || t("common.values.none")}
                  </TableCell>
                  {entraEnabled && (
                    <TableCell className="font-mono text-xs">
                      {role.entra_role_id ? (
                        <Badge
                          variant="secondary"
                          className="font-mono text-xs"
                        >
                          {role.entra_role_id.substring(0, 8)}...
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">
                          {t("admin.roles.page.notSynced")}
                        </span>
                      )}
                    </TableCell>
                  )}
                  <TableCell>
                    <Button
                      variant="link"
                      size="sm"
                      className="h-auto p-0"
                      onClick={() => setViewingPermissions(role)}
                    >
                      {role.name === "super_admin"
                        ? t("admin.roles.page.allPermissions")
                        : t("admin.roles.page.permissionsCount", {
                            count: role.permissions?.length || 0,
                          })}
                    </Button>
                  </TableCell>
                  <TableCell className="text-right space-x-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEditRole(role)}
                    >
                      {t("common.actions.edit")}
                    </Button>
                    {!role.is_system && canDeleteRole && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive hover:text-destructive hover:bg-destructive/10"
                        onClick={() => handleDeleteRole(role)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {/* Create/Edit Role Dialog */}
      <Dialog open={isCreateOpen} onOpenChange={handleCloseCreateDialog}>
        <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingRole
                ? t("admin.roles.page.editDialogTitle")
                : t("admin.roles.page.createDialogTitle")}
            </DialogTitle>
            <DialogDescription>
              {editingRole?.name === "super_admin"
                ? t("admin.roles.page.superAdminDialogDescription")
                : editingRole
                  ? t("admin.roles.page.editDialogDescription")
                  : t("admin.roles.page.createDialogDescription")}
            </DialogDescription>
          </DialogHeader>

          <RoleForm
            role={editingRole || undefined}
            onSubmit={handleSaveRole}
            onCancel={handleCloseCreateDialog}
            isLoading={saveRoleMutation.isPending}
            isSuperAdminEdit={editingRole?.name === "super_admin"}
          />
        </DialogContent>
      </Dialog>

      {/* Entra Manifest Export Dialog */}
      {entraEnabled && (
        <Dialog open={isManifestOpen} onOpenChange={setIsManifestOpen}>
          <DialogContent className="sm:max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{t("admin.roles.manifest.title")}</DialogTitle>
              <DialogDescription>
                {t("admin.roles.manifest.description")}
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-2">
              <Alert>
                <AlertTitle>{t("admin.roles.manifest.alertTitle")}</AlertTitle>
                <AlertDescription>
                  {t("admin.roles.manifest.alertDescription")}
                </AlertDescription>
              </Alert>

              {manifestLoading && (
                <p className="text-sm text-muted-foreground">
                  {t("admin.roles.manifest.generating")}
                </p>
              )}

              {manifestError instanceof Error && (
                <div className="rounded-md bg-destructive/10 p-4">
                  <p className="text-sm font-medium text-destructive">
                    {manifestError.message}
                  </p>
                </div>
              )}

              {!manifestLoading && !manifestError && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">
                      {t("admin.roles.manifest.roleCount", {
                        count: manifestData?.appRoles.length || 0,
                      })}
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyManifest(manifestJson)}
                      disabled={!manifestJson}
                    >
                      <Copy className="mr-2 h-4 w-4" />
                      {copiedManifest === manifestJson
                        ? t("admin.roles.manifest.copied")
                        : t("admin.roles.manifest.copyJson")}
                    </Button>
                  </div>

                  <pre className="max-h-[50vh] overflow-auto rounded-md border bg-muted/40 p-4 text-xs leading-5">
                    {manifestJson}
                  </pre>
                </div>
              )}
            </div>

            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setIsManifestOpen(false)}
              >
                {t("common.actions.close")}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* View Permissions Dialog */}
      <Dialog
        open={!!viewingPermissions}
        onOpenChange={(open) => !open && setViewingPermissions(null)}
      >
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {t("admin.roles.permissions.title", {
                name: viewingPermissions?.name || "",
              })}
            </DialogTitle>
            <DialogDescription>
              {t("admin.roles.permissions.description")}
            </DialogDescription>
          </DialogHeader>

          <div className="py-4">
            {viewingPermissions?.permissions &&
            viewingPermissions.permissions.length > 0 ? (
              <div className="space-y-3">
                {viewingPermissions.permissions.map((permission) => (
                  <div
                    key={permission.id}
                    className="flex items-start gap-3 p-3 rounded-md border"
                  >
                    <div className="flex-1 space-y-1">
                      <div className="font-medium">{permission.name}</div>
                      <div className="text-sm text-muted-foreground">
                        {t("admin.roles.permissions.resource", {
                          resource: permission.resource,
                        })}
                      </div>
                      {permission.description && (
                        <div className="text-sm text-muted-foreground">
                          {permission.description}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground text-center py-8">
                {viewingPermissions?.name === "super_admin"
                  ? t("admin.roles.permissions.superAdminDescription")
                  : t("admin.roles.permissions.empty")}
              </p>
            )}
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setViewingPermissions(null)}
            >
              {t("common.actions.close")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog
        open={!!deleteConfirming}
        onOpenChange={(open) => !open && setDeleteConfirming(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t("admin.roles.delete.title")}</AlertDialogTitle>
            <AlertDialogDescription>
              {t("admin.roles.delete.description", {
                name: deleteConfirming?.name || "",
              })}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleteRoleMutation.isPending}>
              {t("common.actions.cancel")}
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={() =>
                deleteConfirming &&
                deleteRoleMutation.mutate(deleteConfirming.id)
              }
              disabled={deleteRoleMutation.isPending}
              className="bg-destructive hover:bg-destructive/90"
            >
              {deleteRoleMutation.isPending
                ? t("admin.roles.delete.deleting")
                : t("common.actions.delete")}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
