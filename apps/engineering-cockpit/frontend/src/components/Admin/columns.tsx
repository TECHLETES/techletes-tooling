import type { ColumnDef } from "@tanstack/react-table"

import type { RolePublic, UserPublic } from "@/client"
import { Badge } from "@/components/ui/badge"
import i18n from "@/i18n/i18n"
import { cn } from "@/lib/utils"
import { UserActionsMenu } from "./UserActionsMenu"

export type UserTableData = UserPublic & {
  isCurrentUser: boolean
  roles?: RolePublic[]
}

export const columns: ColumnDef<UserTableData>[] = [
  {
    accessorKey: "full_name",
    header: i18n.t("admin.users.columns.fullName"),
    cell: ({ row }) => {
      const fullName = row.original.full_name
      return (
        <div className="flex items-center gap-2">
          <span
            className={cn("font-medium", !fullName && "text-muted-foreground")}
          >
            {fullName || i18n.t("common.values.notAvailable")}
          </span>
          {row.original.isCurrentUser && (
            <Badge variant="outline" className="text-xs">
              {i18n.t("admin.users.columns.you")}
            </Badge>
          )}
        </div>
      )
    },
  },
  {
    accessorKey: "email",
    header: i18n.t("admin.users.columns.email"),
    cell: ({ row }) => (
      <span className="text-muted-foreground">{row.original.email}</span>
    ),
  },
  {
    accessorKey: "is_superuser",
    header: i18n.t("admin.users.columns.role"),
    cell: ({ row }) => {
      const roles = row.original.roles ?? []

      if (roles.length > 0) {
        return (
          <div className="flex flex-wrap gap-2">
            {roles.map((role) => (
              <Badge key={role.id} variant="secondary">
                {role.name}
              </Badge>
            ))}
          </div>
        )
      }

      return (
        <Badge variant={row.original.is_superuser ? "default" : "secondary"}>
          {row.original.is_superuser
            ? i18n.t("admin.users.columns.superuser")
            : i18n.t("admin.users.columns.user")}
        </Badge>
      )
    },
  },
  {
    accessorKey: "is_active",
    header: i18n.t("admin.users.columns.status"),
    cell: ({ row }) => (
      <div className="flex items-center gap-2">
        <span
          className={cn(
            "size-2 rounded-full",
            row.original.is_active ? "bg-success" : "bg-muted-foreground",
          )}
        />
        <span className={row.original.is_active ? "" : "text-muted-foreground"}>
          {row.original.is_active
            ? i18n.t("admin.users.columns.active")
            : i18n.t("admin.users.columns.inactive")}
        </span>
      </div>
    ),
  },
  {
    id: "actions",
    header: () => (
      <span className="sr-only">{i18n.t("common.columns.actions")}</span>
    ),
    cell: ({ row }) => (
      <div className="flex justify-end">
        <UserActionsMenu user={row.original} />
      </div>
    ),
  },
]
