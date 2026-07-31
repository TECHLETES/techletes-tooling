# Frontend Architecture: API > Service > Hooks > Components

## Overview

This document describes the **recommended architectural pattern** for organizing frontend code to maximize reusability, testability, and maintainability. The pattern follows a layered approach:

```
API Client (auto-generated)
  ↓
Services (data logic & API coordination)
  ↓
Hooks (state management & side effects)
  ↓
Components (UI & user interaction)
```

This pattern is **not yet fully implemented** across the codebase but should be used for new features and gradual refactoring.

Form validation schemas are part of the shared frontend schema layer, not component-local logic. Keep `zod` schemas and route search schemas in `frontend/src/schemas/`, and import them into routes, forms, and tests instead of defining `formSchema` or `searchSchema` inline inside `.tsx` files.

---

## Layer 1: API Client

### What It Is
The **auto-generated OpenAPI client** that provides type-safe API calls to the backend.

### Location
```
frontend/src/client/
  generated/
  index.ts  (re-exports all client services)
```

### How to Regenerate
After any backend API changes:
```bash
cd frontend
bun run generate-client  # Regenerates from backend OpenAPI schema
```

### Usage Example

```typescript
import { ItemsService, type ItemPublic } from "@/client"

// Direct API calls (rarely used directly in components)
const items = await ItemsService.readItems({ skip: 0, limit: 10 })
const item = await ItemsService.readItem({ itemId: "123" })
const newItem = await ItemsService.createItem({
  body: {
    title: "New Item",
    description: "Description",
  },
})
```

### Key Points
- **Type-safe**: All responses are TypeScript types
- **Schema-driven**: Types match backend models exactly
- **OpenAPI-compliant**: Generated from backend `/openapi.json`
- **Service classes**: Organized by resource (ItemsService, UsersService, etc.)
- **Never use directly in components** — always go through Services (next layer)

---

## Layer 2: Services

### What Are They?
**Services** are custom business logic wrappers around the API client. They:
- Encapsulate API calls
- Transform/normalize data for frontend use
- Handle error cases uniformly
- Provide a clean contract between API and UI layers
- Enable mocking for tests

### Location
```
frontend/src/services/
  itemsService.ts       # Item-related API logic
  usersService.ts       # User-related API logic
  rolesService.ts       # RBAC API logic
  [resource]Service.ts  # One service per domain
```

### Service Structure Template

```typescript
// frontend/src/services/itemsService.ts

import type { ItemPublic, ItemCreate, ItemUpdate } from "@/client"
import { ItemsService as ApiItemsService } from "@/client"
import { handleError } from "@/utils"

/**
 * Business logic wrapper around Items API.
 * Handles normalization, error handling, and data transformation.
 */
export class ItemsService {
  /**
   * Fetch all items for current user with pagination.
   * Normalizes response into a standard format.
   */
  static async listItems(skip: number = 0, limit: number = 10) {
    try {
      const response = await ApiItemsService.readItems({ skip, limit })
      return {
        items: response.data || [],
        total: response.count || 0,
        hasMore: (skip + limit) < (response.count || 0),
      }
    } catch (error) {
      handleError(error)
      throw new Error("Failed to fetch items")
    }
  }

  /**
   * Get single item by ID.
   */
  static async getItem(itemId: string) {
    try {
      const item = await ApiItemsService.readItem({ itemId })
      if (!item) throw new Error("Item not found")
      return item
    } catch (error) {
      handleError(error)
      throw new Error(`Failed to fetch item ${itemId}`)
    }
  }

  /**
   * Create new item.
   */
  static async createItem(data: ItemCreate) {
    try {
      const newItem = await ApiItemsService.createItem({ body: data })
      return newItem
    } catch (error) {
      handleError(error)
      throw new Error("Failed to create item")
    }
  }

  /**
   * Update existing item.
   */
  static async updateItem(itemId: string, data: Partial<ItemUpdate>) {
    try {
      const updated = await ApiItemsService.updateItem({
        itemId,
        body: data,
      })
      return updated
    } catch (error) {
      handleError(error)
      throw new Error(`Failed to update item ${itemId}`)
    }
  }

  /**
   * Delete item.
   */
  static async deleteItem(itemId: string) {
    try {
      await ApiItemsService.deleteItem({ itemId })
      return true
    } catch (error) {
      handleError(error)
      throw new Error(`Failed to delete item ${itemId}`)
    }
  }

  /**
   * Batch operations.
   */
  static async batchDelete(itemIds: string[]) {
    const results = await Promise.allSettled(
      itemIds.map(id => this.deleteItem(id))
    )
    return {
      succeeded: results.filter(r => r.status === "fulfilled").length,
      failed: results.filter(r => r.status === "rejected").length,
    }
  }
}
```

### Service Best Practices

1. **Static methods or singleton pattern:**
   ```typescript
   // Good: No state
   export class ItemsService {
     static async listItems() { ... }
   }

   // Use:
   const items = await ItemsService.listItems()
   ```

2. **Normalize API responses:**
   ```typescript
   static async listItems() {
     const response = await ApiItemsService.readItems({ ... })
     return {
       items: response.data || [],
       total: response.count || 0,
       hasMore: (skip + limit) < response.count,
     }
   }
   ```

3. **Handle errors consistently:**
   ```typescript
   try {
     return await ApiItemsService.readItem({ itemId })
   } catch (error) {
     handleError(error)  // Logs and shows toast
     throw new Error("Failed to fetch item")
   }
   ```

4. **Type all inputs and outputs:**
   ```typescript
   static async createItem(data: ItemCreate): Promise<ItemPublic> { ... }
   static async deleteItem(itemId: UUID): Promise<boolean> { ... }
   ```

5. **Add JSDoc comments:**
   ```typescript
   /**
    * Fetch items with pagination.
    *
    * @param skip - Number of items to skip
    * @param limit - Max items to return
    * @returns Object with items array, total count, and hasMore flag
    */
   static async listItems(skip: number = 0, limit: number = 10) { ... }
   ```

### Service Composition

Services can call other services:

```typescript
// rolesService.ts
export class RolesService {
  static async getRole(roleId: UUID): Promise<RolePublic> {
    const role = await ApiRbacService.getRole({ roleId })
    return {
      ...role,
      // Enrich role with computed properties
      permissionCount: role.permissions?.length || 0,
    }
  }
}

// itemsService.ts
export class ItemsService {
  static async listItemsWithOwnerRoles(skip: number = 0, limit: number = 10) {
    const itemsData = await this.listItems(skip, limit)

    // Enrich items with owner role info
    const enriched = await Promise.all(
      itemsData.items.map(async (item) => ({
        ...item,
        ownerRole: await RolesService.getUserRole(item.owner_id),
      }))
    )

    return { ...itemsData, items: enriched }
  }
}
```

---

## Layer 3: Hooks

### What Are They?
**Hooks** manage local state, side effects, and integrate with services. They:
- Call services to fetch/update data
- Manage component-level state (loading, errors)
- Handle caching and synchronization (via React Query)
- Provide a clean interface to components

### Location
```
frontend/src/hooks/
  useItems.ts           # Hook for item data
  useUsers.ts           # Hook for user data
  useRoles.ts           # Hook for role data
  use[Feature].ts       # One hook per data domain
```

### Hook Structure Template

```typescript
// frontend/src/hooks/useItems.ts

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { ItemCreate, ItemUpdate } from "@/client"
import { ItemsService } from "@/services/itemsService"
import useCustomToast from "./useCustomToast"

interface UseItemsOptions {
  skip?: number
  limit?: number
  enabled?: boolean
}

/**
 * Hook for managing items data and mutations.
 * Handles fetching, creating, updating, and deleting items.
 */
export function useItems(options: UseItemsOptions = {}) {
  const { skip = 0, limit = 10, enabled = true } = options
  const queryClient = useQueryClient()
  const { showErrorToast, showSuccessToast } = useCustomToast()

  // Fetch items
  const {
    data,
    isLoading,
    error,
    isError,
  } = useQuery({
    queryKey: ["items", skip, limit],
    queryFn: () => ItemsService.listItems(skip, limit),
    enabled,
    retry: 1,
  })

  // Create item
  const createMutation = useMutation({
    mutationFn: (newItem: ItemCreate) => ItemsService.createItem(newItem),
    onSuccess: (newItem) => {
      // Invalidate and refetch list
      queryClient.invalidateQueries({ queryKey: ["items"] })
      showSuccessToast("Item created successfully")
      return newItem
    },
    onError: (error) => {
      const message = error instanceof Error ? error.message : "Unknown error"
      showErrorToast(message)
    },
  })

  // Update item
  const updateMutation = useMutation({
    mutationFn: ({ itemId, data }: { itemId: string; data: Partial<ItemUpdate> }) =>
      ItemsService.updateItem(itemId, data),
    onSuccess: (updated, { itemId }) => {
      // Update specific item in cache
      queryClient.setQueryData(["item", itemId], updated)
      // Invalidate list
      queryClient.invalidateQueries({ queryKey: ["items"] })
      showSuccessToast("Item updated successfully")
      return updated
    },
    onError: (error) => {
      const message = error instanceof Error ? error.message : "Unknown error"
      showErrorToast(message)
    },
  })

  // Delete item
  const deleteMutation = useMutation({
    mutationFn: (itemId: string) => ItemsService.deleteItem(itemId),
    onSuccess: (_, itemId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: ["item", itemId] })
      // Invalidate list
      queryClient.invalidateQueries({ queryKey: ["items"] })
      showSuccessToast("Item deleted successfully")
    },
    onError: (error) => {
      const message = error instanceof Error ? error.message : "Unknown error"
      showErrorToast(message)
    },
  })

  return {
    // Query data
    items: data?.items || [],
    total: data?.total || 0,
    hasMore: data?.hasMore || false,
    isLoading,
    isError,
    error: error instanceof Error ? error.message : null,

    // Mutations
    createItem: createMutation.mutate,
    updateItem: updateMutation.mutate,
    deleteItem: deleteMutation.mutate,

    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,

    createError: createMutation.error,
    updateError: updateMutation.error,
    deleteError: deleteMutation.error,
  }
}
```

### Hook Best Practices

1. **Use React Query for data fetching:**
   ```typescript
   const { data, isLoading, error } = useQuery({
     queryKey: ["items"],
     queryFn: () => ItemsService.listItems(),
   })
   ```

2. **Use React Query for mutations:**
   ```typescript
   const createMutation = useMutation({
     mutationFn: (item: ItemCreate) => ItemsService.createItem(item),
     onSuccess: () => {
       queryClient.invalidateQueries({ queryKey: ["items"] })
     },
   })
   ```

3. **Normalize loading/error states:**
   ```typescript
   return {
     data: data?.items || [],
     isLoading,
     error: error?.message || null,
     isPending: mutation.isPending,
   }
   ```

4. **Cache invalidation:**
   ```typescript
   queryClient.invalidateQueries({ queryKey: ["items"] })
   queryClient.setQueryData(["item", id], updated)
   queryClient.removeQueries({ queryKey: ["item", id] })
   ```

5. **Combine multiple queries:**
   ```typescript
   export function useItemsWithOwners() {
     const items = useItems()
     const owners = useUsers()

     return {
       items: items.items.map(item => ({
         ...item,
         owner: owners.users.find(u => u.id === item.owner_id),
       })),
       isLoading: items.isLoading || owners.isLoading,
     }
   }
   ```

---

## Layer 4: Components

### What Are They?
**Components** are React UI elements that use hooks and services to:
- Display data
- Handle user interaction
- Manage local UI state (form inputs, dropdowns)
- Call mutations on user actions

### Form Validation Schemas
Form schemas belong in `frontend/src/schemas/` and should be reused by any route or component that needs them.

Rules:
- Define `zod` schemas in shared `.ts` files next to the related domain, not inside component or route files.
- Re-export inferred types from the schema file when the form needs a local type alias.
- Keep route `validateSearch` schemas in the same shared schema layer.
- Components should only consume the schema and type; they should not own the validation definition.

### Location
```
frontend/src/components/
  Items/
    ItemList.tsx        # Display list of items
    ItemDetail.tsx      # Show single item
    ItemForm.tsx        # Create/edit item form
    ItemActions.tsx     # Delete, share, etc. buttons
  Users/
    UserList.tsx
    UserProfile.tsx
  [Feature]/
    [Component].tsx
```

### Component Structure Template

```typescript
// frontend/src/components/Items/ItemList.tsx

import { useState } from "react"
import type { ItemPublic } from "@/client"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import useCustomToast from "@/hooks/useCustomToast"
import { useItems } from "@/hooks/useItems"
import ItemActions from "./ItemActions"
import ItemForm from "./ItemForm"

/**
 * Display list of all items with pagination, search, and actions.
 * Uses useItems hook for data fetching and mutations.
 */
export default function ItemList() {
  const [skip, setSkip] = useState(0)
  const [showForm, setShowForm] = useState(false)
  const [selectedItem, setSelectedItem] = useState<ItemPublic | null>(null)

  // Get items via hook
  const {
    items,
    total,
    hasMore,
    isLoading,
    error,
    deleteItem,
    isDeleting,
  } = useItems({ skip, limit: 10 })

  const { showErrorToast } = useCustomToast()

  if (error) {
    return <div className="text-red-500">Error: {error}</div>
  }

  const handleDelete = (itemId: string) => {
    if (confirm("Delete this item?")) {
      deleteItem(itemId)
    }
  }

  const handleNext = () => {
    if (hasMore) setSkip(skip + 10)
  }

  const handlePrev = () => {
    if (skip > 0) setSkip(skip - 10)
  }

  return (
    <div className="space-y-4">
      {/* Header with create button */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Items</h1>
        <Button onClick={() => setShowForm(true)}>New Item</Button>
      </div>

      {/* Form modal/dialog */}
      {showForm && (
        <ItemForm
          onClose={() => setShowForm(false)}
          onSuccess={() => {
            setShowForm(false)
            setSkip(0)  // Reset to first page
          }}
        />
      )}

      {/* Loading state */}
      {isLoading ? (
        <Spinner />
      ) : items.length === 0 ? (
        <p className="text-gray-500">No items found</p>
      ) : (
        <div className="space-y-2">
          {/* List of items */}
          {items.map(item => (
            <div key={item.id} className="flex justify-between items-center p-4 border rounded">
              <div>
                <h3 className="font-bold">{item.title}</h3>
                <p className="text-sm text-gray-600">{item.description}</p>
              </div>

              {/* Actions */}
              <ItemActions
                item={item}
                onDelete={() => handleDelete(item.id)}
                isDeleting={isDeleting}
                onSelect={() => setSelectedItem(item)}
              />
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      <div className="flex justify-between items-center">
        <Button disabled={skip === 0} onClick={handlePrev}>
          Previous
        </Button>
        <span className="text-sm text-gray-600">
          Showing {skip + 1} to {Math.min(skip + 10, total)} of {total}
        </span>
        <Button disabled={!hasMore} onClick={handleNext}>
          Next
        </Button>
      </div>
    </div>
  )
}
```

```typescript
// frontend/src/components/Items/ItemForm.tsx

import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import type { ItemCreate, ItemUpdate, ItemPublic } from "@/client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { useItems } from "@/hooks/useItems"
import useCustomToast from "@/hooks/useCustomToast"

const formSchema = z.object({
  title: z.string().min(1, "Title is required"),
  description: z.string().optional(),
})

type FormData = z.infer<typeof formSchema>

interface ItemFormProps {
  item?: ItemPublic  // For editing
  onClose: () => void
  onSuccess?: (item: ItemPublic) => void
}

export default function ItemForm({ item, onClose, onSuccess }: ItemFormProps) {
  const { createItem, updateItem, isCreating, isUpdating } = useItems()
  const { showErrorToast, showSuccessToast } = useCustomToast()

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      title: item?.title || "",
      description: item?.description || "",
    },
  })

  const onSubmit = (data: FormData) => {
    if (item) {
      // Update existing
      updateItem(
        { itemId: item.id, data: data as Partial<ItemUpdate> },
        {
          onSuccess: () => {
            showSuccessToast("Item updated")
            onSuccess?.(item)
            onClose()
          },
          onError: (error) => {
            showErrorToast("Failed to update item")
          },
        }
      )
    } else {
      // Create new
      createItem(data as ItemCreate, {
        onSuccess: (newItem) => {
          showSuccessToast("Item created")
          onSuccess?.(newItem)
          onClose()
        },
        onError: (error) => {
          showErrorToast("Failed to create item")
        },
      })
    }
  }

  const isLoading = isCreating || isUpdating

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label>Title</label>
        <Input {...form.register("title")} />
        {form.formState.errors.title && (
          <p className="text-red-500 text-sm">{form.formState.errors.title.message}</p>
        )}
      </div>

      <div>
        <label>Description</label>
        <Textarea {...form.register("description")} />
      </div>

      <div className="flex gap-2 justify-end">
        <Button variant="outline" onClick={onClose}>
          Cancel
        </Button>
        <Button disabled={isLoading} type="submit">
          {isLoading ? "Saving..." : item ? "Update" : "Create"}
        </Button>
      </div>
    </form>
  )
}
```

```typescript
// frontend/src/components/Items/ItemActions.tsx

import type { ItemPublic } from "@/client"
import usePermissions from "@/hooks/usePermissions"
import { Button } from "@/components/ui/button"
import { Trash2 } from "lucide-react"

interface ItemActionsProps {
  item: ItemPublic
  onDelete: () => void
  isDeleting: boolean
  onSelect?: (item: ItemPublic) => void
}

export default function ItemActions({
  item,
  onDelete,
  isDeleting,
  onSelect,
}: ItemActionsProps) {
  const { can } = usePermissions()

  return (
    <div className="space-x-2">
      {can("items:read") && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onSelect?.(item)}
        >
          View
        </Button>
      )}

      {can("items:update") && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onSelect?.(item)}
        >
          Edit
        </Button>
      )}

      {can("items:delete") && (
        <Button
          variant="ghost"
          size="sm"
          disabled={isDeleting}
          onClick={onDelete}
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      )}
    </div>
  )
}
```

### Component Best Practices

1. **Always use hooks:**
   ```typescript
   // Good
   const { items, isLoading, error } = useItems()

   // Avoid
   const [items, setItems] = useState([])
   useEffect(() => {
     ItemsService.listItems().then(setItems)
   }, [])
   ```

2. **Separate containers from presentational components:**
   ```typescript
   // ItemListContainer.tsx — uses hooks, manages state
   export default function ItemListContainer() {
     const { items, isLoading } = useItems()
     return <ItemListView items={items} isLoading={isLoading} />
   }

   // ItemListView.tsx — just renders UI
   interface ItemListViewProps {
     items: ItemPublic[]
     isLoading: boolean
   }
   function ItemListView({ items, isLoading }: ItemListViewProps) {
     // Just render
   }
   ```

3. **Handle permissions:**
   ```typescript
   const { can } = usePermissions()

   if (!can("items:delete")) {
     return null  // Hide delete button
   }
   ```

4. **Use loading and error states:**
   ```typescript
   if (isLoading) return <Spinner />
   if (error) return <ErrorMessage error={error} />
   return <ItemList items={items} />
   ```

5. **Compose components:**
   ```typescript
   <div className="space-y-4">
     <ItemSearch />
     <ItemList />
     <ItemPagination />
   </div>
   ```

---

## Data Flow Example: Creating an Item

Here's how data flows through all four layers:

```
1. USER INTERACTION (Component)
   └─→ User clicks "Create Item" button

2. COMPONENT → HOOK (Layer 4 → 3)
   └─→ ItemForm calls createItem() from useItems()

3. HOOK → SERVICE (Layer 3 → 2)
   └─→ useItems() calls ItemsService.createItem()

4. SERVICE → API CLIENT (Layer 2 → 1)
   └─→ ItemsService calls ApiItemsService.createItem()

5. API CLIENT → BACKEND
   └─→ POST /api/v1/items { title, description }

6. BACKEND → API CLIENT (Response)
   └─→ { id, title, description, owner_id, created_at, ... }

7. API CLIENT → SERVICE
   └─→ Return ItemPublic object

8. SERVICE → HOOK
   └─→ Return normalized { item, success }

9. HOOK → COMPONENT
   └─→ Update React Query cache, call onSuccess callback

10. COMPONENT → UI UPDATE
    └─→ Form closes, list refreshes, success toast shown
```

---

## Migration Path

For existing components not following this pattern:

1. **Identify the data domain** (items, users, roles, etc.)

2. **Create/update service:**
   ```bash
   touch frontend/src/services/itemsService.ts
   # Add business logic wrapper around API client
   ```

3. **Create/update hook:**
   ```bash
   touch frontend/src/hooks/useItems.ts
   # Add state management and mutations
   ```

4. **Refactor component:**
   ```typescript
   // Before
   const [items, setItems] = useState([])
   useEffect(() => {
     ItemsService.readItems().then(setItems)
   }, [])

   // After
   const { items } = useItems()
   ```

5. **Add permission checks:**
   ```typescript
   const { can } = usePermissions()
   if (!can("items:delete")) return null
   ```

---

## Testing

### Service Tests

```typescript
// frontend/src/services/__tests__/itemsService.test.ts

import { describe, it, expect, vi } from "vitest"
import { ItemsService } from "../itemsService"
import { ItemsService as ApiItemsService } from "@/client"

vi.mock("@/client", () => ({
  ItemsService: {
    readItems: vi.fn(),
  },
}))

describe("ItemsService", () => {
  it("normalizes API response", async () => {
    vi.mocked(ApiItemsService.readItems).mockResolvedValue({
      data: [{ id: "1", title: "Test" }],
      count: 1,
    })

    const result = await ItemsService.listItems()

    expect(result).toEqual({
      items: [{ id: "1", title: "Test" }],
      total: 1,
      hasMore: false,
    })
  })
})
```

### Hook Tests

```typescript
// frontend/src/hooks/__tests__/useItems.test.ts

import { renderHook, act } from "@testing-library/react"
import { describe, it, expect, vi } from "vitest"
import { useItems } from "../useItems"
import { ItemsService } from "@/services/itemsService"

vi.mock("@/services/itemsService")

describe("useItems", () => {
  it("loads items on mount", async () => {
    const mockItems = [{ id: "1", title: "Test" }]
    vi.mocked(ItemsService.listItems).mockResolvedValue({
      items: mockItems,
      total: 1,
      hasMore: false,
    })

    const { result } = renderHook(() => useItems())

    expect(result.current.isLoading).toBe(true)

    await act(async () => {
      await vi.runAllTimersAsync()
    })

    expect(result.current.items).toEqual(mockItems)
    expect(result.current.isLoading).toBe(false)
  })
})
```

### Component Tests

```typescript
// frontend/src/components/__tests__/ItemList.test.tsx

import { render, screen } from "@testing-library/react"
import { describe, it, expect, vi } from "vitest"
import ItemList from "../Items/ItemList"
import { useItems } from "@/hooks/useItems"

vi.mock("@/hooks/useItems")

describe("ItemList", () => {
  it("renders item list", () => {
    const mockItems = [{ id: "1", title: "Test Item" }]
    vi.mocked(useItems).mockReturnValue({
      items: mockItems,
      isLoading: false,
      total: 1,
      hasMore: false,
      // ... other return values
    })

    render(<ItemList />)

    expect(screen.getByText("Test Item")).toBeInTheDocument()
  })
})
```

---

## File Structure

Complete directory structure for a feature:

```
frontend/src/
  client/
    generated/
      # Auto-generated from OpenAPI
  services/
    itemsService.ts          # Item business logic
    usersService.ts
    rolesService.ts
    index.ts                 # Export all services
  hooks/
    useItems.ts              # Item state & mutations
    useUsers.ts
    useRoles.ts
    __tests__/               # Hook tests
    index.ts                 # Export all hooks
  components/
    Items/
      ItemList.tsx           # Container component
      ItemDetail.tsx
      ItemForm.tsx
      ItemActions.tsx
      __tests__/             # Component tests
    Users/
    Roles/
  pages/                      # or routes/ for TanStack Router
  utils/
  types/
  main.tsx
```

---

## Summary

| Layer | Purpose | Example | Location |
|-------|---------|---------|----------|
| **API Client** | Type-safe API calls | `ItemsService.readItems()` | `frontend/src/client/` |
| **Services** | Business logic & data transformation | `ItemsService.listItems()` | `frontend/src/services/` |
| **Hooks** | State, caching, mutations | `useItems()` | `frontend/src/hooks/` |
| **Components** | UI & user interaction | `<ItemList />` | `frontend/src/components/` |

**Flow**: User → Component → Hook → Service → API Client → Backend

**Benefits**:
- ✅ Separation of concerns
- ✅ Reusability (hooks can be used in multiple components)
- ✅ Testability (services and hooks can be mocked)
- ✅ Type safety (end-to-end TypeScript)
- ✅ Maintainability (clear data flow)
- ✅ Performance (React Query caching)

---

## Code Generation

After implementing this pattern across the app, services and hooks can be auto-generated:

```bash
# Future: Code generator to scaffold services + hooks from OpenAPI schema
bun run generate:services   # Creates itemsService.ts, usersService.ts, etc.
bun run generate:hooks      # Creates useItems.ts, useUsers.ts, etc.
```

This would further reduce boilerplate and keep types in sync with backend.
