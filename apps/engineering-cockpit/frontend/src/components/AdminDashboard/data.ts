import type { LucideIcon } from "lucide-react"
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Layers,
  PlayCircle,
} from "lucide-react"

export type TaskMetricLabelKey =
  | "dashboard.tasks.metrics.totalJobs"
  | "dashboard.tasks.status.queued"
  | "dashboard.tasks.status.running"
  | "dashboard.tasks.status.completed"
  | "dashboard.tasks.status.failed"

export interface TaskMetric {
  labelKey: TaskMetricLabelKey
  value: number
  change?: number
  changeLabel?: string
  icon: LucideIcon
}

export const TASK_METRICS: TaskMetric[] = [
  {
    labelKey: "dashboard.tasks.metrics.totalJobs",
    value: 0,
    icon: Layers,
  },
  {
    labelKey: "dashboard.tasks.status.queued",
    value: 0,
    icon: Clock,
  },
  {
    labelKey: "dashboard.tasks.status.running",
    value: 0,
    icon: PlayCircle,
  },
  {
    labelKey: "dashboard.tasks.status.completed",
    value: 0,
    icon: CheckCircle2,
  },
  {
    labelKey: "dashboard.tasks.status.failed",
    value: 0,
    icon: AlertCircle,
  },
]

export type QueueLevel = "default" | "high" | "low"

export type SampleTaskLabelKey =
  | "dashboard.tasks.samples.sendEmail.label"
  | "dashboard.tasks.samples.exportCsv.label"
  | "dashboard.tasks.samples.exportJson.label"
  | "dashboard.tasks.samples.processFile.label"
  | "dashboard.tasks.samples.processFileHigh.label"

export type SampleTaskDescriptionKey =
  | "dashboard.tasks.samples.sendEmail.description"
  | "dashboard.tasks.samples.exportCsv.description"
  | "dashboard.tasks.samples.exportJson.description"
  | "dashboard.tasks.samples.processFile.description"
  | "dashboard.tasks.samples.processFileHigh.description"

export interface SampleTask {
  labelKey: SampleTaskLabelKey
  descriptionKey: SampleTaskDescriptionKey
  task_type: "send_email" | "export_data" | "process_file"
  queue: QueueLevel
  kwargs: Record<string, unknown>
}

export const SAMPLE_TASKS: SampleTask[] = [
  {
    labelKey: "dashboard.tasks.samples.sendEmail.label",
    descriptionKey: "dashboard.tasks.samples.sendEmail.description",
    task_type: "send_email",
    queue: "default",
    kwargs: {
      to: "test@example.com",
      subject: "Hello from the task queue",
      _body: "This is a test email sent via the background task system.",
    },
  },
  {
    labelKey: "dashboard.tasks.samples.exportCsv.label",
    descriptionKey: "dashboard.tasks.samples.exportCsv.description",
    task_type: "export_data",
    queue: "low",
    kwargs: { user_id: "demo-user", format: "csv" },
  },
  {
    labelKey: "dashboard.tasks.samples.exportJson.label",
    descriptionKey: "dashboard.tasks.samples.exportJson.description",
    task_type: "export_data",
    queue: "low",
    kwargs: { user_id: "demo-user", format: "json" },
  },
  {
    labelKey: "dashboard.tasks.samples.processFile.label",
    descriptionKey: "dashboard.tasks.samples.processFile.description",
    task_type: "process_file",
    queue: "default",
    kwargs: { file_id: "sample-file-001" },
  },
  {
    labelKey: "dashboard.tasks.samples.processFileHigh.label",
    descriptionKey: "dashboard.tasks.samples.processFileHigh.description",
    task_type: "process_file",
    queue: "high",
    kwargs: { file_id: "urgent-file-002" },
  },
]

export const STATUS_FILTER_OPTIONS = [
  "queued",
  "running",
  "completed",
  "failed",
  "cancelled",
] as const

export const QUEUE_FILTER_OPTIONS = ["high", "default", "low"] as const

/** Maps job status to badge variant */
export const STATUS_BADGE_MAP: Record<
  string,
  "success" | "warning" | "danger" | "info" | "neutral"
> = {
  queued: "warning",
  running: "info",
  completed: "success",
  failed: "danger",
  cancelled: "neutral",
}

/** Maps queue priority to badge variant */
export const QUEUE_BADGE_MAP: Record<string, "danger" | "info" | "neutral"> = {
  high: "danger",
  default: "info",
  low: "neutral",
}

/** Chart theme colors using CSS variable references */
export const CHART_COLORS = {
  primary: "var(--chart-1)",
  success: "var(--chart-2)",
  info: "var(--chart-3)",
  warning: "var(--chart-4)",
  danger: "var(--chart-5)",
} as const

export const PIE_CHART_COLORS = [
  CHART_COLORS.primary,
  CHART_COLORS.success,
  CHART_COLORS.info,
  CHART_COLORS.warning,
  CHART_COLORS.danger,
]
