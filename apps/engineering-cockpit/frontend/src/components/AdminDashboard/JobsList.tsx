import { useState } from "react"
import { useTranslation } from "react-i18next"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useAdmin } from "@/hooks/useAdmin"
import {
  QUEUE_FILTER_OPTIONS,
  STATUS_BADGE_MAP,
  STATUS_FILTER_OPTIONS,
} from "./data"

function TableSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-10 w-full rounded-xl" />
      ))}
    </div>
  )
}

export const JobsList = () => {
  const [selectedQueue, setSelectedQueue] = useState<
    "high" | "default" | "low" | undefined
  >(undefined)
  const [selectedStatus, setSelectedStatus] = useState<string | undefined>(
    undefined,
  )

  const { jobsList, isLoadingJobsList } = useAdmin({
    refetchInterval: 5000,
  })
  const { t } = useTranslation()
  const queueLabels = {
    default: t("dashboard.tasks.queue.default"),
    high: t("dashboard.tasks.queue.high"),
    low: t("dashboard.tasks.queue.low"),
  } as const
  const statusLabels = {
    cancelled: t("dashboard.tasks.status.cancelled"),
    completed: t("dashboard.tasks.status.completed"),
    failed: t("dashboard.tasks.status.failed"),
    queued: t("dashboard.tasks.status.queued"),
    running: t("dashboard.tasks.status.running"),
  } as const

  const jobs =
    jobsList?.jobs?.filter((job) => {
      const queueMatch = !selectedQueue || job.queue === selectedQueue
      const statusMatch = !selectedStatus || job.status === selectedStatus
      return queueMatch && statusMatch
    }) || []

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-semibold">
          {t("dashboard.tasks.jobsList.title")}
        </CardTitle>
        <CardDescription className="text-xs">
          {t("dashboard.tasks.jobsList.description")}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Queue Filter */}
          <Tabs
            value={selectedQueue ?? "all"}
            onValueChange={(val) =>
              setSelectedQueue(
                val === "all"
                  ? undefined
                  : (val as (typeof QUEUE_FILTER_OPTIONS)[number]),
              )
            }
          >
            <TabsList>
              <TabsTrigger value="all">
                {t("dashboard.tasks.jobsList.allQueues")}
              </TabsTrigger>
              {QUEUE_FILTER_OPTIONS.map((q) => (
                <TabsTrigger key={q} value={q} className="capitalize">
                  {t("dashboard.tasks.jobsList.queuePriority", {
                    queue: queueLabels[q],
                  })}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>

          {/* Status Filter */}
          <div className="flex gap-2 flex-wrap">
            <Badge
              variant={selectedStatus === undefined ? "default" : "outline"}
              className="cursor-pointer"
              onClick={() => setSelectedStatus(undefined)}
            >
              {t("dashboard.tasks.jobsList.allStatuses")}
            </Badge>
            {STATUS_FILTER_OPTIONS.map((status) => (
              <Badge
                key={status}
                variant={selectedStatus === status ? "default" : "outline"}
                className="cursor-pointer capitalize"
                onClick={() => setSelectedStatus(status)}
              >
                {statusLabels[status]}
              </Badge>
            ))}
          </div>

          {/* Jobs Table */}
          {isLoadingJobsList ? (
            <TableSkeleton />
          ) : jobs.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t("common.fields.jobId")}</TableHead>
                    <TableHead>{t("common.fields.taskType")}</TableHead>
                    <TableHead>{t("common.fields.status")}</TableHead>
                    <TableHead>{t("common.fields.queue")}</TableHead>
                    <TableHead>{t("common.fields.created")}</TableHead>
                    <TableHead>{t("common.fields.started")}</TableHead>
                    <TableHead>{t("common.fields.ended")}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {jobs.map((job) => (
                    <TableRow key={job.id}>
                      <TableCell className="font-mono text-xs">
                        {job.id.slice(0, 12)}…
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {job.func}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={STATUS_BADGE_MAP[job.status] ?? "neutral"}
                          className="capitalize"
                        >
                          {
                            statusLabels[
                              job.status as keyof typeof statusLabels
                            ]
                          }
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm capitalize">
                        {queueLabels[job.queue as keyof typeof queueLabels]}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground tabular-nums">
                        {job.created_at
                          ? new Date(job.created_at).toLocaleTimeString()
                          : "–"}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground tabular-nums">
                        {job.started_at
                          ? new Date(job.started_at).toLocaleTimeString()
                          : "–"}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground tabular-nums">
                        {job.ended_at
                          ? new Date(job.ended_at).toLocaleTimeString()
                          : "–"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="flex h-32 items-center justify-center text-sm text-muted-foreground">
              {t("dashboard.tasks.jobsList.empty")}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
