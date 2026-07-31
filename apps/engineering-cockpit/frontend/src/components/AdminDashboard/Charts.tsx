import { useTranslation } from "react-i18next"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import ChartCard from "@/components/Common/ChartCard"
import MetricCard from "@/components/Common/MetricCard"
import { Skeleton } from "@/components/ui/skeleton"
import { useAdmin } from "@/hooks/useAdmin"
import { CHART_COLORS, TASK_METRICS } from "./data"

function MetricsSkeleton() {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-28 rounded-2xl" />
      ))}
    </div>
  )
}

export const JobStatusChart = () => {
  const { jobStats, isLoadingJobStats } = useAdmin()
  const { t } = useTranslation()
  const statusLabels = {
    cancelled: t("dashboard.tasks.status.cancelled"),
    completed: t("dashboard.tasks.status.completed"),
    failed: t("dashboard.tasks.status.failed"),
    queued: t("dashboard.tasks.status.queued"),
    running: t("dashboard.tasks.status.running"),
  } as const

  if (isLoadingJobStats) {
    return (
      <ChartCard
        title={t("dashboard.tasks.charts.statusDistribution.title")}
        description={t("dashboard.tasks.charts.statusDistribution.description")}
      >
        <Skeleton className="h-64 w-full rounded-xl" />
      </ChartCard>
    )
  }
  if (!jobStats) return null

  const STATUS_COLORS: Record<string, string> = {
    queued: CHART_COLORS.info,
    running: CHART_COLORS.warning,
    completed: CHART_COLORS.success,
    failed: CHART_COLORS.danger,
    cancelled: CHART_COLORS.primary,
  }

  const chartData = [
    {
      key: "queued" as const,
      name: statusLabels.queued,
      value: jobStats.status_counts.queued,
    },
    {
      key: "running" as const,
      name: statusLabels.running,
      value: jobStats.status_counts.running,
    },
    {
      key: "completed" as const,
      name: statusLabels.completed,
      value: jobStats.status_counts.completed,
    },
    {
      key: "failed" as const,
      name: statusLabels.failed,
      value: jobStats.status_counts.failed,
    },
    {
      key: "cancelled" as const,
      name: statusLabels.cancelled,
      value: jobStats.status_counts.cancelled,
    },
  ].filter((item) => (item.value ?? 0) > 0)

  return (
    <ChartCard
      title={t("dashboard.tasks.charts.statusDistribution.title")}
      description={t("dashboard.tasks.charts.statusDistribution.description")}
    >
      {chartData.length > 0 ? (
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, value }) => `${name}: ${value}`}
              outerRadius={100}
              fill={CHART_COLORS.primary}
              dataKey="value"
              strokeWidth={2}
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={STATUS_COLORS[entry.key] ?? CHART_COLORS.primary}
                />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                borderRadius: "0.75rem",
                border: "1px solid var(--border)",
                background: "var(--card)",
                color: "var(--card-foreground)",
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      ) : (
        <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
          {t("dashboard.tasks.charts.emptyJobs")}
        </div>
      )}
    </ChartCard>
  )
}

export const QueueDistributionChart = () => {
  const { jobStats, isLoadingJobStats } = useAdmin({
    refetchInterval: 5000,
  })
  const { t } = useTranslation()
  const queueLabels = {
    default: t("dashboard.tasks.queue.default"),
    high: t("dashboard.tasks.queue.high"),
    low: t("dashboard.tasks.queue.low"),
  } as const

  if (isLoadingJobStats) {
    return (
      <ChartCard
        title={t("dashboard.tasks.charts.queueDistribution.title")}
        description={t("dashboard.tasks.charts.queueDistribution.description")}
      >
        <Skeleton className="h-64 w-full rounded-xl" />
      </ChartCard>
    )
  }
  if (!jobStats) return null

  const chartData = jobStats.queue_stats

  return (
    <ChartCard
      title={t("dashboard.tasks.charts.queueDistribution.title")}
      description={t("dashboard.tasks.charts.queueDistribution.description")}
    >
      {chartData && chartData.length > 0 ? (
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--border)"
              strokeOpacity={0.5}
            />
            <XAxis
              dataKey="name"
              tickFormatter={(value: keyof typeof queueLabels) =>
                queueLabels[value]
              }
              tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
              axisLine={{ stroke: "var(--border)" }}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                borderRadius: "0.75rem",
                border: "1px solid var(--border)",
                background: "var(--card)",
                color: "var(--card-foreground)",
              }}
            />
            <Bar
              dataKey="count"
              fill={CHART_COLORS.primary}
              radius={[6, 6, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
          {t("dashboard.tasks.charts.emptyQueues")}
        </div>
      )}
    </ChartCard>
  )
}

export const JobsStatsSummary = () => {
  const { jobStats, isLoadingJobStats } = useAdmin({
    refetchInterval: 5000,
  })
  const { t } = useTranslation()
  const metricLabels = {
    "dashboard.tasks.metrics.totalJobs": t("dashboard.tasks.metrics.totalJobs"),
    "dashboard.tasks.status.completed": t("dashboard.tasks.status.completed"),
    "dashboard.tasks.status.failed": t("dashboard.tasks.status.failed"),
    "dashboard.tasks.status.queued": t("dashboard.tasks.status.queued"),
    "dashboard.tasks.status.running": t("dashboard.tasks.status.running"),
  } as const

  if (isLoadingJobStats) return <MetricsSkeleton />
  if (!jobStats) return null

  const { status_counts, total_jobs } = jobStats

  const values = [
    total_jobs,
    status_counts.queued,
    status_counts.running,
    status_counts.completed,
    status_counts.failed,
  ]

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
      {TASK_METRICS.map((metric, i) => (
        <MetricCard
          key={metric.labelKey}
          label={metricLabels[metric.labelKey]}
          value={values[i] ?? 0}
          icon={metric.icon}
        />
      ))}
    </div>
  )
}
