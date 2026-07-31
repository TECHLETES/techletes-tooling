import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Package } from "lucide-react"
import { Suspense } from "react"
import { useTranslation } from "react-i18next"
import { DataTable } from "@/components/Common/DataTable"
import AddItem from "@/components/Items/AddItem"
import { columns } from "@/components/Items/columns"
import PendingItems from "@/components/Pending/PendingItems"
import { Card, CardContent } from "@/components/ui/card"
import i18n from "@/i18n/i18n"
import { ItemsService } from "@/services"

function getItemsQueryOptions() {
  return {
    queryFn: () => ItemsService.listItems(0, 100),
    queryKey: ["items"],
  }
}

export const Route = createFileRoute("/_layout/items")({
  component: Items,
  head: () => ({
    meta: [
      {
        title: `${i18n.t("items.page.metaTitle")} - Techletes`,
      },
    ],
  }),
})

function ItemsTableContent() {
  const { data: items } = useSuspenseQuery(getItemsQueryOptions())
  const { t } = useTranslation()

  if (items.items.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center text-center py-16">
          <div className="rounded-full bg-muted p-4 mb-4">
            <Package className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold">
            {t("items.page.emptyTitle")}
          </h3>
          <p className="text-sm text-muted-foreground mb-4">
            {t("items.page.emptyDescription")}
          </p>
          <AddItem />
        </CardContent>
      </Card>
    )
  }

  return <DataTable columns={columns} data={items.items} />
}

function ItemsTable() {
  return (
    <Suspense fallback={<PendingItems />}>
      <ItemsTableContent />
    </Suspense>
  )
}

function Items() {
  const { t } = useTranslation()

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            {t("items.page.title")}
          </h1>
          <p className="text-sm text-muted-foreground">
            {t("items.page.subtitle")}
          </p>
        </div>
        <AddItem />
      </div>
      <ItemsTable />
    </div>
  )
}
