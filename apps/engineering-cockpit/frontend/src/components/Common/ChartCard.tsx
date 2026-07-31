import type { FC, ReactNode } from "react"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface ChartCardProps {
  title: string
  description?: string
  children: ReactNode
  className?: string
  action?: ReactNode
}

const ChartCard: FC<ChartCardProps> = ({
  title,
  description,
  children,
  className,
  action,
}) => {
  return (
    <Card className={cn("py-5", className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-sm font-semibold">{title}</CardTitle>
            {description && (
              <CardDescription className="text-xs">
                {description}
              </CardDescription>
            )}
          </div>
          {action}
        </div>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  )
}

export default ChartCard
