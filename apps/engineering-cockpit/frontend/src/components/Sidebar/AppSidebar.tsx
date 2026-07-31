import { Briefcase, Home, Shield, Users, Zap } from "lucide-react"
import { useMemo } from "react"
import { useTranslation } from "react-i18next"
import { Logo } from "@/components/Common/Logo"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
} from "@/components/ui/sidebar"
import useAuth from "@/hooks/useAuth"
import usePermissions from "@/hooks/usePermissions"
import { type Item, Main } from "./Main"
import { User } from "./User"

export function AppSidebar() {
  const { user: currentUser, isSuperAdmin } = useAuth()
  const { can } = usePermissions()
  const { t } = useTranslation()

  const primaryItems = useMemo<Item[]>(
    () => [
      { icon: Home, title: t("nav.primary.dashboard"), path: "/" },
      { icon: Briefcase, title: t("nav.primary.items"), path: "/items" },
    ],
    [t],
  )

  const allAdminItems = useMemo<Item[]>(
    () => [
      {
        icon: Users,
        title: t("nav.admin.users"),
        path: "/admin/users",
        permission: "users:read",
      },
      {
        icon: Shield,
        title: t("nav.admin.roles"),
        path: "/admin/roles",
        permission: "rbac:view_roles",
      },
      { icon: Zap, title: t("nav.admin.tasks"), path: "/admin-tasks" },
    ],
    [t],
  )

  // Filter admin items based on permissions
  const adminItems = useMemo(() => {
    if (!currentUser) return []

    // Super admin can see all admin items
    if (isSuperAdmin()) {
      return allAdminItems
    }

    // Regular users see only items they have permission for
    return allAdminItems.filter((item) => {
      if (!("permission" in item) || !item.permission) return true
      return can(item.permission)
    })
  }, [currentUser, isSuperAdmin, can, allAdminItems])

  // Show admin section only if user is Super admin or has admin permissions
  const showAdminSection =
    isSuperAdmin() ||
    can("users:read") ||
    can("rbac:view_roles") ||
    can("admin:manage_tasks")

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="px-4 py-6 group-data-[collapsible=icon]:px-0 group-data-[collapsible=icon]:items-center">
        <Logo variant="responsive" />
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            {t("nav.groups.menu")}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <Main items={primaryItems} />
          </SidebarGroupContent>
        </SidebarGroup>
        {showAdminSection && adminItems.length > 0 && (
          <SidebarGroup>
            <SidebarGroupLabel className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              {t("nav.groups.admin")}
            </SidebarGroupLabel>
            <SidebarGroupContent>
              <Main items={adminItems} />
            </SidebarGroupContent>
          </SidebarGroup>
        )}
      </SidebarContent>
      <SidebarFooter>
        <User user={currentUser} />
      </SidebarFooter>
    </Sidebar>
  )
}

export default AppSidebar
