import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Bell, Shield, Users } from "lucide-react"
import { Suspense, useState } from "react"
import { useTranslation } from "react-i18next"
import { createRouteGuard } from "@/auth/roleGuard"
import type { UserPublic } from "@/client"
import AddUser from "@/components/Admin/AddUser"
import { columns, type UserTableData } from "@/components/Admin/columns"
import { DataTable } from "@/components/Common/DataTable"
import MetricCard from "@/components/Common/MetricCard"
import PendingUsers from "@/components/Pending/PendingUsers"
import { Button } from "@/components/ui/button"
import useAuth from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import i18n from "@/i18n/i18n"
import { NotificationsService, UsersService } from "@/services"

function getUsersQueryOptions() {
  return {
    queryFn: () => UsersService.listUsers(0, 100),
    queryKey: ["users"],
  }
}

export const Route = createFileRoute("/_layout/admin/users")({
  component: UsersPage,
  beforeLoad: createRouteGuard({
    requiredPermissions: ["rbac:manage_users"],
  }),
  head: () => ({
    meta: [
      {
        title: `${i18n.t("admin.users.page.metaTitle")} - Techletes`,
      },
    ],
  }),
})

function UsersTableContent() {
  const { user: currentUser } = useAuth()
  const { data: users } = useSuspenseQuery(getUsersQueryOptions())

  const tableData: UserTableData[] = users.users.map((user: UserPublic) => ({
    ...user,
    isCurrentUser: currentUser?.id === user.id,
  }))

  return <DataTable columns={columns} data={tableData} />
}

function UsersTable() {
  return (
    <Suspense fallback={<PendingUsers />}>
      <UsersTableContent />
    </Suspense>
  )
}

function TestNotificationButton() {
  const [isLoading, setIsLoading] = useState(false)
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const { t } = useTranslation()

  const handleSendTestNotification = async () => {
    setIsLoading(true)
    try {
      const response = await NotificationsService.sendTestNotificationToAll()
      showSuccessToast(response.message)
    } catch (error) {
      showErrorToast(
        error instanceof Error
          ? error.message
          : t("admin.users.page.testNotificationError"),
      )
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Button
      onClick={handleSendTestNotification}
      disabled={isLoading}
      variant="outline"
    >
      <Bell className="h-4 w-4" />
      {isLoading
        ? t("admin.users.page.sendingNotification")
        : t("admin.users.page.sendNotification")}
    </Button>
  )
}

function UserStats() {
  const { data: users } = useSuspenseQuery(getUsersQueryOptions())
  const { t } = useTranslation()
  const total = users.users.length
  const superusers = users.users.filter((u) => u.is_superuser).length
  const active = users.users.filter((u) => u.is_active).length

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <MetricCard
        label={t("admin.users.stats.total")}
        value={String(total)}
        icon={Users}
        iconClassName="bg-primary/10 text-primary"
      />
      <MetricCard
        label={t("admin.users.stats.active")}
        value={String(active)}
        icon={Shield}
        iconClassName="bg-success/10 text-success"
      />
      <MetricCard
        label={t("admin.users.stats.superusers")}
        value={String(superusers)}
        icon={Shield}
        iconClassName="bg-warning/10 text-warning"
      />
    </div>
  )
}

function UsersPage() {
  const { t } = useTranslation()

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            {t("admin.users.page.title")}
          </h1>
          <p className="text-sm text-muted-foreground">
            {t("admin.users.page.subtitle")}
          </p>
        </div>
        <div className="flex gap-2">
          <TestNotificationButton />
          <AddUser />
        </div>
      </div>

      <Suspense
        fallback={
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="h-24 rounded-2xl bg-card border animate-pulse"
              />
            ))}
          </div>
        }
      >
        <UserStats />
      </Suspense>

      <UsersTable />
    </div>
  )
}
