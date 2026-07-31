import { zodResolver } from "@hookform/resolvers/zod"
import { useMemo } from "react"
import { useForm } from "react-hook-form"
import { useTranslation } from "react-i18next"
import { isEntraEnabled } from "@/auth/entra"
import type { RoleCreate, RolePublic, RoleUpdate } from "@/client"
import PermissionSelector from "@/components/Admin/PermissionSelector"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
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
import { Textarea } from "@/components/ui/textarea"
import { useRoles } from "@/hooks/useRoles"
import { type RoleFormData, roleFormSchema } from "@/schemas/admin"

/**
 * Props for RoleForm component
 */
interface RoleFormProps {
  /** Optional role for edit mode */
  role?: RolePublic
  /** Callback when form is submitted */
  onSubmit: (data: RoleCreate | RoleUpdate) => Promise<void>
  /** Callback when form is cancelled */
  onCancel: () => void
  /** Whether the form is currently submitting */
  isLoading?: boolean
  /** Whether this is Super admin edit mode (only show entra_role_id) */
  isSuperAdminEdit?: boolean
}

/**
 * Form component for creating and editing roles.
 * Includes role name, description, and permission selector.
 */
export const RoleForm = ({
  role,
  onSubmit,
  onCancel,
  isLoading = false,
  isSuperAdminEdit = false,
}: RoleFormProps) => {
  const { permissions, isLoadingPermissions } = useRoles({
    enabled: !isSuperAdminEdit,
  })
  const { t } = useTranslation()

  // Preselect permission IDs from existing role
  const preselectedPermissions = useMemo(
    () => role?.permissions?.map((p) => p.id) || [],
    [role],
  )

  // Initialize form with single schema for all modes
  const form = useForm<RoleFormData>({
    resolver: zodResolver(roleFormSchema),
    mode: "onBlur",
    defaultValues: {
      name: role?.name || "",
      description: role?.description || "",
      permission_ids: preselectedPermissions,
      entra_role_id: role?.entra_role_id || "",
    },
  })

  /**
   * Handle form submission
   */
  const handleFormSubmit = async (data: RoleFormData) => {
    // IMPORTANT: Validate permissions are selected only in normal edit mode (not Super admin)
    if (
      !isSuperAdminEdit &&
      (!data.permission_ids || data.permission_ids.length === 0)
    ) {
      form.setError("permission_ids", {
        message: t("validation.permissionRequired"),
      })
      return
    }

    try {
      if (isSuperAdminEdit) {
        // IMPORTANT: Super admin updates must only send entra_role_id.
        // Sending name/description/permission_ids causes the backend guard to reject the request.
        await onSubmit({
          entra_role_id: data.entra_role_id || null,
        })
        return
      }

      await onSubmit({
        name: data.name,
        description: data.description || null,
        permission_ids: data.permission_ids,
        entra_role_id: data.entra_role_id || null,
      })
    } catch (_error) {
      // Error handling is done in the parent component
    }
  }

  const isEditMode = !!role
  const entraEnabled = isEntraEnabled()

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(handleFormSubmit)}
        className="space-y-6"
      >
        {!isSuperAdminEdit && entraEnabled && (
          <Alert>
            <AlertTitle>{t("admin.roles.form.entraEnabledTitle")}</AlertTitle>
            <AlertDescription>
              {isEditMode
                ? t("admin.roles.form.entraEnabledEditDescription")
                : t("admin.roles.form.entraEnabledCreateDescription")}
            </AlertDescription>
          </Alert>
        )}

        {isSuperAdminEdit && (
          <Alert>
            <AlertTitle>{t("admin.roles.form.superAdminTitle")}</AlertTitle>
            <AlertDescription>
              {t("admin.roles.form.superAdminDescription")}
            </AlertDescription>
          </Alert>
        )}

        {!isSuperAdminEdit && (
          <>
            {/* Role Name Field */}
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("common.fields.roleName")} *</FormLabel>
                  <FormControl>
                    <Input
                      placeholder={t("admin.roles.form.roleNamePlaceholder")}
                      {...field}
                      disabled={isLoading || isLoadingPermissions}
                      readOnly={isEditMode && role?.name === "super_admin"}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Description Field */}
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("common.fields.description")}</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder={t("admin.roles.form.descriptionPlaceholder")}
                      {...field}
                      value={field.value || ""}
                      disabled={isLoading || isLoadingPermissions}
                      readOnly={isEditMode && role?.name === "super_admin"}
                      className="resize-none"
                      rows={3}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Entra Role ID Field (edit mode only) */}
            {entraEnabled && isEditMode && (
              <FormField
                control={form.control}
                name="entra_role_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("common.fields.entraRoleId")}</FormLabel>
                    <FormControl>
                      <Input
                        placeholder={t(
                          "admin.roles.form.entraRoleIdPlaceholder",
                        )}
                        {...field}
                        value={field.value || ""}
                        disabled={isLoading || isLoadingPermissions}
                        className="font-mono text-xs"
                      />
                    </FormControl>
                    <p className="text-xs text-muted-foreground mt-1">
                      {t("admin.roles.form.entraRoleIdHelp")}
                    </p>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

            {/* Super admin Role Badge */}
            {isEditMode && role?.name === "super_admin" && (
              <div className="p-3 bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800 rounded-md">
                <p className="text-sm text-amber-900 dark:text-amber-100">
                  {t("admin.roles.form.superAdminLocked")}
                </p>
              </div>
            )}

            {/* Permissions Selector */}
            <FormField
              control={form.control}
              name="permission_ids"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("common.fields.permissions")} *</FormLabel>
                  <FormControl>
                    <PermissionSelector
                      selectedPermissionIds={field.value}
                      onSelectionChange={field.onChange}
                      availablePermissions={permissions}
                      disabled={
                        isLoading ||
                        isLoadingPermissions ||
                        (isEditMode && role?.name === "super_admin")
                      }
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </>
        )}

        {isSuperAdminEdit && entraEnabled && (
          <FormField
            control={form.control}
            name="entra_role_id"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t("common.fields.entraRoleId")}</FormLabel>
                <FormControl>
                  <Input
                    placeholder={t(
                      "admin.roles.form.superAdminEntraPlaceholder",
                    )}
                    {...field}
                    value={field.value || ""}
                    disabled={isLoading}
                    className="font-mono text-xs"
                  />
                </FormControl>
                <p className="text-xs text-muted-foreground mt-1">
                  {t("admin.roles.form.superAdminEntraHelp")}
                </p>
                <FormMessage />
              </FormItem>
            )}
          />
        )}

        {/* Form Actions */}
        <div className="flex gap-3 justify-end">
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={isLoading || isLoadingPermissions}
          >
            {t("common.actions.cancel")}
          </Button>
          {/* IMPORTANT: LoadingButton disabled state should NOT disable Super admin edit.
              We now allow editing Super admin roles (entra_role_id field only).
              Only disable during loading/submission. */}
          <LoadingButton
            type="submit"
            loading={isLoading || isLoadingPermissions}
          >
            {isEditMode
              ? t("common.actions.update")
              : t("common.actions.create")}
          </LoadingButton>
        </div>
      </form>
    </Form>
  )
}

export default RoleForm
