import { useState } from "react"
import { useTranslation } from "react-i18next"
import type { TaskCreate } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { useTasks } from "@/hooks/useTasks"
import { QUEUE_BADGE_MAP, SAMPLE_TASKS, type SampleTask } from "./data"

interface TaskButtonProps {
  task: SampleTask
}

const TaskButton = ({ task }: TaskButtonProps) => {
  const { enqueueTask, isCreating } = useTasks()
  const [lastJobId, setLastJobId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const { t } = useTranslation()
  const queueLabels = {
    default: t("dashboard.tasks.queue.default"),
    high: t("dashboard.tasks.queue.high"),
    low: t("dashboard.tasks.queue.low"),
  } as const
  const taskLabels = {
    "dashboard.tasks.samples.exportCsv.label": t(
      "dashboard.tasks.samples.exportCsv.label",
    ),
    "dashboard.tasks.samples.exportJson.label": t(
      "dashboard.tasks.samples.exportJson.label",
    ),
    "dashboard.tasks.samples.processFile.label": t(
      "dashboard.tasks.samples.processFile.label",
    ),
    "dashboard.tasks.samples.processFileHigh.label": t(
      "dashboard.tasks.samples.processFileHigh.label",
    ),
    "dashboard.tasks.samples.sendEmail.label": t(
      "dashboard.tasks.samples.sendEmail.label",
    ),
  } as const
  const taskDescriptions = {
    "dashboard.tasks.samples.exportCsv.description": t(
      "dashboard.tasks.samples.exportCsv.description",
    ),
    "dashboard.tasks.samples.exportJson.description": t(
      "dashboard.tasks.samples.exportJson.description",
    ),
    "dashboard.tasks.samples.processFile.description": t(
      "dashboard.tasks.samples.processFile.description",
    ),
    "dashboard.tasks.samples.processFileHigh.description": t(
      "dashboard.tasks.samples.processFileHigh.description",
    ),
    "dashboard.tasks.samples.sendEmail.description": t(
      "dashboard.tasks.samples.sendEmail.description",
    ),
  } as const

  const handleEnqueueTask = async () => {
    try {
      setError(null)
      const result = await enqueueTask({
        task_type: task.task_type,
        queue: task.queue,
        kwargs: task.kwargs,
      } as TaskCreate)
      setLastJobId(result.id)
    } catch (_err) {
      setError(t("dashboard.tasks.feedback.enqueueError"))
    }
  }

  return (
    <div className="flex flex-col gap-2 rounded-xl border bg-card p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <div className="mb-1 flex items-center gap-2">
            <span className="text-sm font-medium">
              {taskLabels[task.labelKey]}
            </span>
            <Badge variant={QUEUE_BADGE_MAP[task.queue] ?? "neutral"}>
              {queueLabels[task.queue]}
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground">
            {taskDescriptions[task.descriptionKey]}
          </p>
        </div>
        <Button
          size="sm"
          onClick={handleEnqueueTask}
          disabled={isCreating}
          className="shrink-0"
        >
          {isCreating
            ? t("dashboard.tasks.actions.queuing")
            : t("dashboard.tasks.actions.run")}
        </Button>
      </div>
      {lastJobId && (
        <p className="text-xs font-mono text-success">
          {t("dashboard.tasks.feedback.queued", {
            jobId: `${lastJobId.slice(0, 16)}…`,
          })}
        </p>
      )}
      {error && <p className="text-xs text-destructive">✗ {error}</p>}
    </div>
  )
}

export const SampleTaskButtons = () => {
  const { enqueueTask, isCreating } = useTasks()
  const [runAllError, setRunAllError] = useState<string | null>(null)
  const [runAllSuccess, setRunAllSuccess] = useState(false)
  const { t } = useTranslation()

  const handleRunAll = async () => {
    try {
      setRunAllError(null)
      setRunAllSuccess(false)
      await Promise.all(
        SAMPLE_TASKS.map((task) =>
          enqueueTask({
            task_type: task.task_type,
            queue: task.queue,
            kwargs: task.kwargs,
          } as TaskCreate),
        ),
      )
      setRunAllSuccess(true)
    } catch (_err) {
      setRunAllError(t("dashboard.tasks.feedback.queueSomeError"))
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-sm font-semibold">
              {t("dashboard.tasks.samples.title")}
            </CardTitle>
            <CardDescription className="text-xs">
              {t("dashboard.tasks.samples.description")}
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRunAll}
            disabled={isCreating}
          >
            {isCreating
              ? t("dashboard.tasks.actions.queuingAll")
              : t("dashboard.tasks.actions.runAll")}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {SAMPLE_TASKS.map((task) => (
            <TaskButton
              key={`${task.task_type}-${task.queue}-${task.labelKey}`}
              task={task}
            />
          ))}
        </div>
        {runAllSuccess && (
          <p className="mt-3 text-xs text-success">
            {t("dashboard.tasks.feedback.allQueued", {
              count: SAMPLE_TASKS.length,
            })}
          </p>
        )}
        {runAllError && (
          <p className="mt-3 text-xs text-destructive">✗ {runAllError}</p>
        )}
      </CardContent>
    </Card>
  )
}
