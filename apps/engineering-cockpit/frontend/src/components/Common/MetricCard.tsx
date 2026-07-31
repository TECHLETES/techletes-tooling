import { type LucideIcon, TrendingDown, TrendingUp } from "lucide-react"
import type { FC } from "react"

import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface MetricCardProps {
  label: string
  value: string | number
  change?: number
  changeLabel?: string
  icon?: LucideIcon
  iconClassName?: string
  className?: string
}

const MetricCard: FC<MetricCardProps> = ({
  label,
  value,
  change,
  changeLabel,
  icon: Icon,
  iconClassName,
  className,
}) => {
  const isPositive = change !== undefined && change >= 0
  const TrendIcon = isPositive ? TrendingUp : TrendingDown

  return (
    <Card className={cn("py-5", className)}>
      <CardContent className="flex items-start justify-between">
        <div className="flex flex-col gap-1">
          <span className="text-sm font-medium text-muted-foreground">
            {label}
          </span>
          <span className="text-2xl font-semibold tabular-nums tracking-tight">
            {value}
          </span>
          {change !== undefined && (
            <div className="flex items-center gap-1 text-xs">
              <TrendIcon
                className={cn(
                  "size-3.5",
                  isPositive ? "text-success" : "text-destructive",
                )}
              />
              <span
                className={cn(
                  "font-medium",
                  isPositive ? "text-success" : "text-destructive",
                )}
              >
                {isPositive ? "+" : ""}
                {change}%
              </span>
              {changeLabel && (
                <span className="text-muted-foreground">{changeLabel}</span>
              )}
            </div>
          )}
        </div>
        {Icon && (
          <div
            className={cn(
              "rounded-xl bg-primary/10 p-2.5 text-primary",
              iconClassName,
            )}
          >
            <Icon className="size-5" />
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default MetricCard
