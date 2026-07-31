import { useMemo, useState } from "react"
import { useTranslation } from "react-i18next"
import type { PermissionPublic } from "@/client"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ScrollArea } from "@/components/ui/scroll-area"

/**
 * Props for PermissionSelector component
 */
interface PermissionSelectorProps {
  /** List of selected permission IDs */
  selectedPermissionIds: string[]
  /** Callback when selection changes */
  onSelectionChange: (permissionIds: string[]) => void
  /** List of available permissions */
  availablePermissions: PermissionPublic[]
  /** Whether the selector is disabled */
  disabled?: boolean
}

/**
 * Multi-select component for assigning permissions to roles.
 * Displays permissions grouped by resource category with search/filter functionality.
 */
export const PermissionSelector = ({
  selectedPermissionIds,
  onSelectionChange,
  availablePermissions,
  disabled = false,
}: PermissionSelectorProps) => {
  const [searchQuery, setSearchQuery] = useState("")
  const { t } = useTranslation()

  // Group permissions by resource
  const groupedPermissions = useMemo(() => {
    const groups: Record<string, PermissionPublic[]> = {}

    availablePermissions.forEach((permission) => {
      if (!groups[permission.resource]) {
        groups[permission.resource] = []
      }
      groups[permission.resource].push(permission)
    })

    // Sort groups alphabetically
    return Object.keys(groups)
      .sort()
      .reduce(
        (result, key) => {
          result[key] = groups[key].sort((a, b) => a.name.localeCompare(b.name))
          return result
        },
        {} as Record<string, PermissionPublic[]>,
      )
  }, [availablePermissions])

  // Filter permissions based on search query
  const filteredGroups = useMemo(() => {
    if (!searchQuery) return groupedPermissions

    const query = searchQuery.toLowerCase()
    const filtered: Record<string, PermissionPublic[]> = {}

    Object.entries(groupedPermissions).forEach(([resource, permissions]) => {
      const matches = permissions.filter(
        (p) =>
          p.name.toLowerCase().includes(query) ||
          p.description?.toLowerCase().includes(query) ||
          resource.toLowerCase().includes(query),
      )

      if (matches.length > 0) {
        filtered[resource] = matches
      }
    })

    return filtered
  }, [groupedPermissions, searchQuery])

  // Count selected and total permissions in filtered results
  const filterStats = useMemo(() => {
    let total = 0
    let selected = 0

    Object.values(filteredGroups).forEach((permissions) => {
      permissions.forEach((p) => {
        total++
        if (selectedPermissionIds.includes(p.id)) {
          selected++
        }
      })
    })

    return { selected, total }
  }, [filteredGroups, selectedPermissionIds])

  /**
   * Handle permission checkbox change
   */
  const handlePermissionChange = (permissionId: string, checked: boolean) => {
    const newSelection = checked
      ? [...selectedPermissionIds, permissionId]
      : selectedPermissionIds.filter((id) => id !== permissionId)

    onSelectionChange(newSelection)
  }

  /**
   * Select all permissions in the filtered results
   */
  const handleSelectAll = () => {
    const allIds = Object.values(filteredGroups)
      .flat()
      .map((p) => p.id)

    const newSelection = Array.from(
      new Set([...selectedPermissionIds, ...allIds]),
    )
    onSelectionChange(newSelection)
  }

  /**
   * Deselect all permissions in the filtered results
   */
  const handleDeselectAll = () => {
    const visibleIds = new Set(
      Object.values(filteredGroups)
        .flat()
        .map((p) => p.id),
    )

    const newSelection = selectedPermissionIds.filter(
      (id) => !visibleIds.has(id),
    )
    onSelectionChange(newSelection)
  }

  return (
    <div className="space-y-4">
      {/* Search input */}
      <Input
        placeholder={t("permissions.selector.searchPlaceholder")}
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        disabled={disabled}
        className="h-9"
      />

      {/* Select/Deselect all buttons */}
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleSelectAll}
          disabled={disabled || filterStats.total === 0}
        >
          {t("permissions.selector.selectAll")}
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={handleDeselectAll}
          disabled={disabled || filterStats.selected === 0}
        >
          {t("permissions.selector.deselectAll")}
        </Button>
        {filterStats.total > 0 && (
          <span className="ml-auto text-xs text-muted-foreground pt-2">
            {t("permissions.selector.selectedCount", {
              selected: filterStats.selected,
              total: filterStats.total,
            })}
          </span>
        )}
      </div>

      {/* Permissions list */}
      <ScrollArea className="h-96 rounded-md border">
        <div className="p-4 space-y-6">
          {Object.entries(filteredGroups).length === 0 ? (
            <div className="text-sm text-muted-foreground text-center py-8">
              {t("permissions.selector.empty")}
            </div>
          ) : (
            Object.entries(filteredGroups).map(([resource, permissions]) => (
              <div key={resource} className="space-y-3">
                {/* Resource category header */}
                <h4 className="font-medium text-sm px-2 py-1 rounded bg-muted">
                  {resource}
                </h4>

                {/* Permissions in this category */}
                <div className="space-y-2 pl-2">
                  {permissions.map((permission) => (
                    <div key={permission.id} className="flex items-start gap-3">
                      <Checkbox
                        id={permission.id}
                        checked={selectedPermissionIds.includes(permission.id)}
                        onCheckedChange={(checked) =>
                          handlePermissionChange(
                            permission.id,
                            checked === true,
                          )
                        }
                        disabled={disabled}
                        className="mt-1"
                      />
                      <Label
                        htmlFor={permission.id}
                        className="flex-1 cursor-pointer"
                      >
                        <div className="font-sm font-medium leading-tight">
                          {permission.name}
                        </div>
                        {permission.description && (
                          <div className="text-xs text-muted-foreground leading-tight">
                            {permission.description}
                          </div>
                        )}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  )
}

export default PermissionSelector
