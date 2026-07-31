import { createFileRoute } from "@tanstack/react-router"
import { useTranslation } from "react-i18next"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import useAuth from "@/hooks/useAuth"
import i18n from "@/i18n/i18n"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({
    meta: [
      {
        title: `${i18n.t("dashboard.home.metaTitle")} - Techletes`,
      },
    ],
  }),
})

function Dashboard() {
  const { user: currentUser } = useAuth()
  const { t } = useTranslation()
  const displayName = currentUser?.full_name || currentUser?.email || ""

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight truncate max-w-sm">
          {t("dashboard.home.greeting", { name: displayName })}
        </h1>
        <p className="text-sm text-muted-foreground">
          {t("dashboard.home.subtitle")}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-semibold">
            {t("dashboard.home.gettingStarted.title")}
          </CardTitle>
          <CardDescription className="text-xs">
            {t("dashboard.home.gettingStarted.description")}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            {t("dashboard.home.gettingStarted.body")}
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
