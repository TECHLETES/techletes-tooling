---
name: Frontend Pattern Guidelines
description: Component structure, hooks patterns, client code generation, API integration, and testing for React frontend
applyTo: frontend/src/**/*.tsx, frontend/src/**/*.ts, frontend/tests/**/*.ts
---

# Frontend Development Instructions

## Design Reference

**All UI/UX decisions must align with [frontend/design-brief.json](../frontend/design-brief.json).**

This design brief is the authoritative reference for:
- Layout system and responsive breakpoints
- Component design patterns (cards, buttons, forms, tables, charts)
- Color system (brand orange, neutral grays, accent colors)
- Typography and spacing tokens
- Dark mode adaptations
- Interaction patterns and states
- Accessibility requirements

When creating new components or modifying existing ones, consult the design brief for:
- Spacing and padding values
- Radius values for cards and buttons
- Color usage and contrast requirements
- Font sizes and weights
- Responsive behavior
- Interactive states (hover, active, disabled)

## Project Setup & Configuration

### TypeScript Configuration

**Strict mode enabled** — all files use strict type checking:

```json
{
  "compilerOptions": {
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "jsx": "react-jsx",
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

**Key Rules:**
- ✅ Use `@/` import alias for absolute imports
- ✅ No unused variables or parameters (enforced by strict mode)
- ✅ Explicit return types on functions
- ✅ No implicit `any` types
- ❌ No class components (use hooks only)
- ❌ No direct runtime API client calls in components or hooks; use `@/services`

### Vite Configuration

**Fast refresh enabled** — HMR (hot module reloading) in development:

```typescript
// vite.config.ts
export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  plugins: [
    tanstackRouter({
      target: "react",
      autoCodeSplitting: true,
    }),
    react(),
    tailwindcss(),
  ],
})
```

**Environment Variables:**
- Base API URL: `VITE_API_URL` (e.g., `http://localhost:8000/api/v1`)
- Override in `.env.local`

---

## OpenAPI Client Generation

### Generate Client from Backend

When backend API changes, regenerate the TypeScript client:

```bash
cd frontend
bun run generate-client
# Regenerates: src/client/schemas.gen.ts, sdk.gen.ts, types.gen.ts
```

**Flow:**
1. Backend generates OpenAPI schema at `/openapi.json`
2. Config: `openapi-ts.config.ts` points to `./openapi.json`
3. OpenAPI TS generates the low-level API client in `src/client/`
4. App-facing service wrappers in `src/services/` normalize and consume the generated client
5. Types from backend Pydantic models auto-imported in `src/client/types.gen.ts`

### Client Structure

`src/client/index.ts` exports:

```typescript
// Re-exports from generated files
export { ApiError } from './core/ApiError';
export { OpenAPI } from './core/OpenAPI';
export * from './sdk.gen';        // Service classes (UsersService, ItemsService, etc.)
export * from './types.gen';      // All Pydantic types from backend
```

### Using Services

**Service Pattern** — Components should use the app service layer, not the generated client directly:

```typescript
import { AuthService, ItemsService, UsersService } from "@/services"
import type { ItemPublic } from "@/client"

// List items through the service layer
const itemsResponse = await ItemsService.listItems(0, 10)
const items = itemsResponse.items

// Create item through the service layer
const newItem = await ItemsService.createItem({
  title: "New Item",
  description: "A description",
})

// Get current user through the service layer
const currentUser = await UsersService.getCurrentUser()

// Login
const response = await AuthService.loginWithAccessToken({
  username: "user@example.com",
  password: "password",
})
```

Use the generated client only in `src/services/` and test utilities. Components and hooks should consume the service layer or hooks built on top of it.

**Authentication:**
- Token stored in `localStorage` as `access_token`
- Set in `main.tsx` via `OpenAPI.TOKEN` callback
- Auto-injected in request headers

### Type Imports

All types are auto-generated from Pydantic models:

```typescript
import type {
  UserPublic,
  ItemPublic,
  UserCreate,
  ItemCreate,
  UsersPublic,
  ItemsPublic,
} from "@/client"

interface UserProfile {
  user: UserPublic
  items: ItemPublic[]
}
```

**No manual type declarations** — always import from `@/client`.
Runtime calls should go through `@/services`; only type imports should come directly from `@/client`.

---

## Component Structure

### Component File Organization

Organize components by feature/domain:

```
src/components/
  Admin/          # Admin panel components
    AddUser.tsx
    DeleteUser.tsx
    EditUser.tsx
    UserActionsMenu.tsx
    columns.tsx
  Items/          # Item list and detail
    ItemList.tsx
    ItemDetail.tsx
  UserSettings/   # User settings pages
    SettingsForm.tsx
  Common/         # Shared across domains
    ErrorComponent.tsx
    NotFound.tsx
  ui/             # Primitive UI components (buttons, forms, dialogs)
    button.tsx
    dialog.tsx
    form.tsx
    input.tsx
    loading-button.tsx
    # ... shadcn/ui primitives
```

### Component Patterns

**Functional Components with Hooks:**

```typescript
import { FC, ReactNode } from "react"
import type { UserPublic } from "@/client"

interface UserCardProps {
  user: UserPublic
  onDelete?: (id: string) => void
  children?: ReactNode
}

const UserCard: FC<UserCardProps> = ({ user, onDelete, children }) => {
  return (
    <div className="rounded-lg border p-4">
      <h3 className="font-semibold">{user.full_name}</h3>
      <p className="text-sm text-gray-600">{user.email}</p>
      {onDelete && (
        <button onClick={() => onDelete(user.id)}>Delete</button>
      )}
      {children}
    </div>
  )
}

export default UserCard
```

**Key Patterns:**
- Use typed props interfaces with plain function components
- Prefer `function ComponentName(props: Props)` or typed arrow functions
- Optional handlers should be optional in the props type
- Children prop is fine for composition
- Export as default unless the file is intentionally re-exported elsewhere

### Loading States & Buttons

Always provide visual feedback during async operations:

```typescript
import { LoadingButton } from "@/components/ui/loading-button"

const MyForm = () => {
  const { createItem, isCreating } = useItems()

  return (
    <form onSubmit={(e) => {
      e.preventDefault()
      createItem(formData)
    }}>
      <LoadingButton
        type="submit"
        disabled={isCreating}
        loading={isCreating}
      >
        {isCreating ? "Creating..." : "Create Item"}
      </LoadingButton>
    </form>
  )
}
```

---

## Custom Hooks

### useAuth Hook

Centralized authentication state and mutations:

```typescript
import useAuth from "@/hooks/useAuth"

const MyComponent = () => {
  const { user, loginMutation, logout, signUpMutation } = useAuth()

  // user: UserPublic | null (logged-in user data)
  // loginMutation: UseMutationResult for login
  // signUpMutation: UseMutationResult for signup
  // logout: () => void (clears token, redirects to /login)

  return (
    <>
      {user ? (
        <div>Welcome, {user.full_name}!</div>
      ) : (
        <div>Please log in</div>
      )}
    </>
  )
}
```

**Implementation Details:**
- Uses `.queryKey = ["currentUser"]` to cache user data
- Respects `isLoggedIn()` check before fetching
- Auto-invalidates queries on logout
- Handles JWT token in localStorage

### useCustomToast Hook

Consistent toast notifications:

```typescript
import useCustomToast from "@/hooks/useCustomToast"

const MyComponent = () => {
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const handleSuccess = () => {
    showSuccessToast("User created successfully!")
  }

  const handleError = () => {
    showErrorToast("Failed to create user. Check your input.")
  }

  return <>...</>
}
```

**Usage in Mutations:**

```typescript
const { showErrorToast } = useCustomToast()

const mutation = useMutation({
  mutationFn: (data: ItemCreate) => ItemsService.createItem(data),
  onSuccess: () => {
    showSuccessToast("Item created!")
    queryClient.invalidateQueries({ queryKey: ["items"] })
  },
  onError: (err: ApiError) => {
    const message = extractErrorMessage(err)
    showErrorToast(message)
  },
})
```

### Custom Toast Hook Pattern

Create domain-specific hooks that reuse `useCustomToast` and the service layer:

```typescript
// hooks/useUserActions.ts
import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { UserCreate } from "@/client"
import { UsersService } from "@/services"
import useCustomToast from "./useCustomToast"

export const useUserActions = () => {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const createUserMutation = useMutation({
    mutationFn: (data: UserCreate) => UsersService.createUser(data),
    onSuccess: () => {
      showSuccessToast("User created successfully!")
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
    onError: (err) => {
      showErrorToast(extractErrorMessage(err))
    },
  })

  return { createUserMutation }
}
```

---

## Forms with React Hook Form & Zod

### Form Validation Schema

Define validation with Zod:

```typescript
import { z } from "zod"

const userFormSchema = z.object({
  email: z.email({ message: "Invalid email address" }),
  full_name: z.string().optional(),
  password: z
    .string()
    .min(8, { message: "Password must be at least 8 characters" }),
  confirm_password: z.string(),
  is_superuser: z.boolean().default(false),
}).refine((data) => data.password === data.confirm_password, {
  message: "Passwords don't match",
  path: ["confirm_password"],
})

type UserFormData = z.infer<typeof userFormSchema>
```

### Form Component

Use React Hook Form with shadcn/ui Form wrapper:

```typescript
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

const UserForm = ({ onSuccess }: { onSuccess: () => void }) => {
  const form = useForm<UserFormData>({
    resolver: zodResolver(userFormSchema),
    defaultValues: {
      email: "",
      full_name: "",
      password: "",
      confirm_password: "",
      is_superuser: false,
    },
  })

  const onSubmit = async (data: UserFormData) => {
    try {
      await UsersService.createUser(data)
      onSuccess()
    } catch (err) {
      form.setError("root", { message: "Failed to create user" })
    }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input {...field} type="email" />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        {/* More fields... */}
        <Button type="submit">Create User</Button>
      </form>
    </Form>
  )
}

export default UserForm
```

**Key Patterns:**
- Define schema separately from component
- Use `zodResolver` for integration
- Field-level validation: `<FormMessage />`
- Root-level errors: `form.setError("root", { message: "..." })`
- Type inference: `z.infer<typeof schema>`

---

## TanStack Router

### File-Based Routing

Routes generated from file structure in `src/routes/`:

```
src/routes/
  __root.tsx            → Root layout <Outlet />
  _layout.tsx           → Shared layout (sidebar, header)
  _layout/
    index.tsx           → / (home/dashboard)
    admin.tsx           → /admin parent layout
    admin/index.tsx     → /admin default page
    admin/users.tsx     → /admin/users
    admin/roles.tsx     → /admin/roles
    items.tsx           → /items
    settings.tsx        → /settings
    unauthorized.tsx    → /unauthorized
    admin-tasks.tsx     → /admin-tasks
  login.tsx             → /login (outside _layout)
  signup.tsx            → /signup
  recover-password.tsx  → /recover-password
  reset-password.tsx    → /reset-password
  auth/github/callback.tsx → OAuth callback
```

### Root Route

Entry point with providers and error boundaries:

```typescript
// src/routes/__root.tsx
import { createRootRoute, HeadContent, Outlet } from "@tanstack/react-router"
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools"
import { ReactQueryDevtools } from "@tanstack/react-query-devtools"
import ErrorComponent from "@/components/Common/ErrorComponent"
import NotFound from "@/components/Common/NotFound"

export const Route = createRootRoute({
  component: () => (
    <>
      <HeadContent />
      <Outlet />
      <TanStackRouterDevtools position="bottom-right" />
      <ReactQueryDevtools initialIsOpen={false} />
    </>
  ),
  notFoundComponent: () => <NotFound />,
  errorComponent: () => <ErrorComponent />,
})
```

### Nested Routes

Protected layouts for authenticated pages:

```typescript
// src/routes/_layout.tsx
import { createFileRoute, Outlet } from "@tanstack/react-router"
import Sidebar from "@/components/Sidebar"
import { useAuth } from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout")({
  component: Layout,
  beforeLoad: ({ location }) => {
    // Redirect to login if not authenticated
    if (!isLoggedIn()) {
      throw redirect({
        to: "/login",
        search: { redirect: location.href },
      })
    }
  },
})

function Layout() {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
```

### Nested Route Rules

- Parent layout routes like `/_layout/admin` must render `<Outlet />`.
- Put default child behavior in `index.tsx`, not in the parent route.
- Keep route-specific guards on the leaf route when children need different permissions.
- If a child route shows blank, check the parent `<Outlet />` first, then `routeTree.gen.ts`.

### Page Routes

Individual pages within layouts:

```typescript
// src/routes/_layout/items.tsx
import { createFileRoute } from "@tanstack/react-router"
import ItemList from "@/components/Items/ItemList"
import { useItems } from "@/hooks/useItems"

export const Route = createFileRoute("/_layout/items")({
  component: ItemsPage,
})

function ItemsPage() {
  const { items, isLoading } = useItems({ skip: 0, limit: 100 })

  if (isLoading) return <div>Loading...</div>

  return <ItemList items={items} />
}
```

### Navigation

Use `useNavigate` hook:

```typescript
import { useNavigate } from "@tanstack/react-router"

const MyComponent = () => {
  const navigate = useNavigate()

  const handleClick = () => {
    navigate({ to: "/items/$id", params: { id: "123" } })
  }

  return <button onClick={handleClick}>View Item</button>
}
```

---

## Data Fetching with React Query

### Query Pattern

Fetch and cache data in hooks, then consume the hook in components:

```typescript
import { useItems } from "@/hooks/useItems"

const MyComponent = () => {
  const { items, isLoading, error } = useItems({ skip: 0, limit: 10 })

  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error: {error.message}</div>

  return (
    <div>
      {items.map((item) => (
        <div key={item.id}>{item.title}</div>
      ))}
    </div>
  )
}
```

**Query Key Conventions:**
- `["resource"]` — list all
- `["resource", id]` — single item
- `["resource", { filter: value }]` — filtered list
- Keys include all parameters that affect the data
- Prefer wrapping `useQuery` in feature hooks such as `useItems`, `useUsers`, `useRoles`, `useTasks`, and `useAdmin`

### Mutation Pattern

Create/update/delete data:

```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { ItemCreate } from "@/client"
import { ItemsService } from "@/services"

const MyComponent = () => {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const mutation = useMutation({
    mutationFn: (data: ItemCreate) => ItemsService.createItem(data),
    onSuccess: (newItem) => {
      showSuccessToast("Item created!")
      // Invalidate cache so list query refetches
      queryClient.invalidateQueries({ queryKey: ["items"] })
    },
    onError: (err: ApiError) => {
      showErrorToast(extractErrorMessage(err))
    },
  })

  const handleCreate = (data: ItemCreate) => {
    mutation.mutate(data)
  }

  return (
    <button
      onClick={() => handleCreate({ title: "New" })}
      disabled={mutation.isPending}
    >
      {mutation.isPending ? "Creating..." : "Create"}
    </button>
  )
}
```

### Error Handling

Global error handler in `main.tsx`:

```typescript
const handleApiError = (error: Error) => {
  if (error instanceof ApiError && [401, 403].includes(error.status)) {
    // Clear token and redirect to login on auth errors
    localStorage.removeItem("access_token")
    window.location.href = "/login"
  }
}

const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: handleApiError,
  }),
  mutationCache: new MutationCache({
    onError: handleApiError,
  }),
})
```

---

## Styling with Tailwind CSS & shadcn/ui

### Theme Provider

Dark/light mode support:

```typescript
import { ThemeProvider } from "@/components/theme-provider"

ReactDOM.createRoot(document.getElementById("root")!).render(
  <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
    {/* App content */}
  </ThemeProvider>
)
```

### Using shadcn/ui Components

Pre-built, customizable components from Radix UI + Tailwind:

```typescript
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Dialog, DialogContent, DialogDescription } from "@/components/ui/dialog"

const MyPage = () => (
  <Card>
    <CardHeader>
      <CardTitle>My Form</CardTitle>
    </CardHeader>
    <CardContent>
      <Input placeholder="Enter name" />
      <Button>Submit</Button>
    </CardContent>
  </Card>
)
```

### Custom Components

Extend shadcn/ui or create primitives:

```typescript
// src/components/ui/loading-button.tsx
import { Button } from "@/components/ui/button"
import { Loader2 } from "lucide-react"
import type { ButtonHTMLAttributes } from "react"

interface LoadingButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  loading?: boolean
}

export const LoadingButton = ({ loading, disabled, children, ...props }: LoadingButtonProps) => (
  <Button {...props} disabled={disabled || loading}>
    {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
    {children}
  </Button>
)
```

---

## Testing with Playwright

### Test Setup

Shared authentication state (`tests/auth.setup.ts`):

```typescript
import { test as setup } from "@playwright/test"
import { firstSuperuser, firstSuperuserPassword } from "./config.ts"

const authFile = "playwright/.auth/user.json"

setup("authenticate", async ({ page }) => {
  await page.goto("/login")
  await page.getByTestId("email-input").fill(firstSuperuser)
  await page.getByTestId("password-input").fill(firstSuperuserPassword)
  await page.getByRole("button", { name: "Log In" }).click()
  await page.waitForURL("/")
  await page.context().storageState({ path: authFile })
})
```

**Configuration** (`playwright.config.ts`):

```typescript
export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'setup', testMatch: /.*\.setup\.ts/ },
    {
      name: 'chromium',
      use: { storageState: 'playwright/.auth/user.json' },
      dependencies: ['setup'],
    },
  ],
})
```

### Page Tests

E2E tests using Playwright API:

```typescript
import { expect, test, type Page } from "@playwright/test"
import { firstSuperuser, firstSuperuserPassword } from "./config.ts"

test("Log in with valid credentials", async ({ page }) => {
  await page.goto("/login")

  await page.getByTestId("email-input").fill(firstSuperuser)
  await page.getByTestId("password-input").fill(firstSuperuserPassword)
  await page.getByRole("button", { name: "Log In" }).click()

  await page.waitForURL("/")
  await expect(page.getByText("Welcome back")).toBeVisible()
})

test("Create item from admin panel", async ({ page }) => {
  await page.goto("/admin")

  await page.getByRole("button", { name: "Add Item" }).click()
  await page.getByLabel("Title").fill("Test Item")
  await page.getByLabel("Description").fill("A test item")
  await page.getByRole("button", { name: "Create" }).click()

  await expect(page.getByText("Item created successfully")).toBeVisible()
  await expect(page.getByText("Test Item")).toBeVisible()
})
```

**Test Best Practices:**
- Use `getByTestId()` for elements you control (add `data-testid="xyz"`)
- Use `getByRole()` for accessible queries (buttons, headings, etc.)
- Use `getByText()` for text content
- Always `await` page actions (no race conditions)
- Use `page.waitForURL()` after navigation
- Use `page.waitForLoadState()` for async content

### Test Utilities

API helpers for complex flows:

```typescript
// tests/utils/privateApi.ts
import { ApiClient } from "@/client"
import type { ItemCreate } from "@/client"

export const createItem = async (
  client: ApiClient,
  item: ItemCreate
) => {
  return await client.ItemsService.createItem({ body: item })
}

export const deleteItem = async (client: ApiClient, itemId: string) => {
  return await client.ItemsService.deleteItem({ itemId })
}

// tests/items.spec.ts
import { test, expect } from "@playwright/test"
import { createItem } from "./utils/privateApi"

test("View created item", async ({ page, context }) => {
  const client = new ApiClient({ ... })
  const item = await createItem(client, { title: "Test" })

  await page.goto(`/items/${item.id}`)
  await expect(page.getByText("Test")).toBeVisible()
})
```

---

## Error Handling

### Global Error Boundary

Catch unhandled React errors:

```typescript
// src/components/Common/ErrorComponent.tsx
import { useRouteContext } from "@tanstack/react-router"

export default function ErrorComponent() {
  const { error } = useRouteContext()

  return (
    <div className="p-4">
      <h1>Oops! Something went wrong.</h1>
      <p className="text-sm text-gray-600">{error?.message}</p>
      <a href="/">Go back home</a>
    </div>
  )
}
```

### API Error Extraction

Helper to extract meaningful messages:

```typescript
import { ApiError } from "@/client"
import { AxiosError } from "axios"

export const extractErrorMessage = (err: ApiError): string => {
  if (err instanceof AxiosError) {
    return err.message
  }

  // Backend returns validation errors as array
  const errDetail = (err.body as any)?.detail
  if (Array.isArray(errDetail) && errDetail.length > 0) {
    return errDetail[0].msg
  }

  return errDetail || "Something went wrong."
}

export const handleError = function (
  this: (msg: string) => void,
  err: ApiError
) {
  const errorMessage = extractErrorMessage(err)
  this(errorMessage)
}
```

**Usage:**

```typescript
const { showErrorToast } = useCustomToast()

const mutation = useMutation({
  mutationFn: (data: ItemCreate) => ItemsService.createItem(data),
  onError: (err: ApiError) => {
    const message = extractErrorMessage(err)
    showErrorToast(message)
  },
})
```

---

## Common Patterns & Best Practices

### useMemo for Filtered Lists

Memoize expensive computations:

```typescript
import { useMemo } from "react"

const ItemList = ({ items, searchTerm }: { items: ItemPublic[]; searchTerm: string }) => {
  const filteredItems = useMemo(
    () => items.filter(item => item.title.includes(searchTerm)),
    [items, searchTerm]
  )

  return <div>{filteredItems.map(item => <div key={item.id}>{item.title}</div>)}</div>
}
```

### useCallback for Event Handlers

Prevent unnecessary re-renders:

```typescript
const handleDelete = useCallback(async (id: string) => {
  try {
    await ItemsService.deleteItem({ itemId: id })
    showSuccessToast("Item deleted!")
    queryClient.invalidateQueries({ queryKey: ["items"] })
  } catch (err) {
    showErrorToast(extractErrorMessage(err))
  }
}, [queryClient, showSuccessToast, showErrorToast])
```

### Composition over Props Drilling

Use component composition instead of passing props deeply:

```typescript
// ❌ Bad: props drilling
function Page({ user, items, onDelete, onEdit }) {
  return <List user={user} items={items} onDelete={onDelete} onEdit={onEdit} />
}

// ✅ Good: composition
function Page() {
  const { user } = useAuth()
  return (
    <List>
      {items.map(item => (
        <ItemRow key={item.id} item={item} />
      ))}
    </List>
  )
}
```

---

## Common Pitfalls

| Issue | Problem | Solution |
|-------|---------|----------|
| **Stale queries** | User sees old data | Use query invalidation on mutations |
| **Missing await** | Race conditions in tests | Always `await` page actions |
| **Prop drilling** | Long dependency chains | Use composition with children |
| **Type mismatch** | TS errors from API changes | Regenerate client with `bun run generate-client` |
| **Auth lost on refresh** | Token not persisted | Use `localStorage` with OpenAPI.TOKEN callback |
| **Multiple queries same key** | Cache collisions | Use specific query keys with params |
| **Unused variables** | TS strict mode errors | Remove unused deps or use `_` prefix |
| **No error handling** | UI freezes on API errors | Always use `onError` in mutations |
| **Hard-coded test data** | Tests fail in different envs | Use `tests/config.ts` and test utilities |
| **Memory leaks** | Subscriptions not cleaned up | Use cleanup in useEffect returns |

---

## Quick Checklist: Adding a New Page

- [ ] Create route file in `src/routes/` (e.g., `src/routes/_layout/mypage.tsx`)
- [ ] Create component in `src/components/MyPage/`
- [ ] Use typed imports: `import type { ItemPublic } from "@/client"`
- [ ] Fetch data with a feature hook such as `useItems()`, `useUsers()`, or `useRoles()`
- [ ] Handle loading/error states
- [ ] Add forms with Zod schema + react-hook-form if needed
- [ ] Use `useCustomToast()` for feedback
- [ ] Style with Tailwind + shadcn/ui
- [ ] Link from sidebar in `src/components/Sidebar/`
- [ ] Add E2E test in `tests/mypage.spec.ts`
- [ ] Update backend if API changes needed
- [ ] Run `bun run generate-client` after backend changes
- [ ] Run `bun run lint` to check TypeScript and formatting
- [ ] Run `bun run typecheck` to verify strict TypeScript
- [ ] Test with `bun run test` or `bun run test:ui`

---

## Quick Reference: Hooks Lifecycle

**Component Mount** → Queries fetch data → Component renders → onSuccess/onError → Re-render
**User Action** → Mutation triggered → Loading state → onSuccess/onError → Invalidate queries → Re-fetch

Use this to understand data flow and when to add observers, invalidations, and callbacks.

---

## Links & References

- [React Docs](https://react.dev)
- [TanStack Router Docs](https://tanstack.com/router/latest)
- [React Query Docs](https://tanstack.com/query/latest)
- [React Hook Form Docs](https://react-hook-form.com)
- [Zod Docs](https://zod.dev)
- [shadcn/ui Components](https://ui.shadcn.com)
- [Tailwind CSS](https://tailwindcss.com)
- [Playwright Docs](https://playwright.dev)
- [OpenAPI TS Generator](https://github.com/hey-api/openapi-ts)
