import { createFileRoute, Outlet, redirect } from "@tanstack/react-router"
import { Search } from "lucide-react"
import { useTranslation } from "react-i18next"
import { Appearance } from "@/components/Common/Appearance"
import { Footer } from "@/components/Common/Footer"
import { LanguageSwitcher } from "@/components/Common/LanguageSwitcher"
import { NotificationBell } from "@/components/Common/NotificationBell"
import AppSidebar from "@/components/Sidebar/AppSidebar"
import { Input } from "@/components/ui/input"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout")({
  component: Layout,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/login",
      })
    }
  },
})

function Layout() {
  const { t } = useTranslation()

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="sticky top-0 z-10 flex h-14 shrink-0 items-center gap-3 border-b bg-card px-4 md:px-6">
          <SidebarTrigger className="-ml-1 text-muted-foreground" />
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              placeholder={t("layout.searchPlaceholder")}
              className="pl-9 h-8 bg-muted/50 border-transparent focus-visible:bg-background"
            />
          </div>
          <div className="ml-auto flex items-center gap-1">
            <NotificationBell />
            <Appearance />
            <LanguageSwitcher />
          </div>
        </header>
        <main className="flex-1 p-4 md:p-6 lg:p-7">
          <div className="mx-auto max-w-7xl">
            <Outlet />
          </div>
        </main>
        <Footer />
      </SidebarInset>
    </SidebarProvider>
  )
}
