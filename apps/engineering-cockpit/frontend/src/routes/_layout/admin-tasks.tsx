import { createFileRoute } from "@tanstack/react-router"
import { useTranslation } from "react-i18next"
import {
  JobStatusChart,
  JobsList,
  JobsStatsSummary,
  QueueDistributionChart,
  SampleTaskButtons,
} from "@/components/AdminDashboard"
import i18n from "@/i18n/i18n"

export const Route = createFileRoute("/_layout/admin-tasks")({
  component: AdminTasksDashboard,
  head: () => ({
    meta: [
      {
        title: `${i18n.t("dashboard.tasks.page.metaTitle")} - Fullstack Template`,
      },
    ],
  }),
})

function AdminTasksDashboard() {
  const { t } = useTranslation()

  return (
    <div className="flex flex-col gap-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          {t("dashboard.tasks.page.title")}
        </h1>
        <p className="text-sm text-muted-foreground">
          {t("dashboard.tasks.page.subtitle")}
        </p>
      </div>

      {/* Metric tiles */}
      <JobsStatsSummary />

      {/* Sample task launcher */}
      <SampleTaskButtons />

      {/* Charts grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <JobStatusChart />
        <QueueDistributionChart />
      </div>

      {/* Jobs list table */}
      <JobsList />
    </div>
  )
}
