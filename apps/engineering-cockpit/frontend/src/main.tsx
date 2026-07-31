import { MsalProvider } from "@azure/msal-react"
import {
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query"
import { createRouter, RouterProvider } from "@tanstack/react-router"
import { StrictMode } from "react"
import ReactDOM from "react-dom/client"
import { loadConsolidatedAuthConfig } from "./auth/consolidatedConfig"
import { getMsalInstance, initEntra, isEntraEnabled } from "./auth/entra"
import { initGithub } from "./auth/github"
import { GoogleOAuthProvider, initGoogle, isGoogleEnabled } from "./auth/google"
import { ApiError, OpenAPI } from "./client"
import { ThemeProvider } from "./components/theme-provider"
import { Toaster } from "./components/ui/sonner"
import { resetBrowserStateForDeployment } from "./lib/deployment-state"
import { clearSessionMarker } from "./lib/session"
import "./i18n/i18n"
import "./index.css"
import { getApiBaseUrl } from "./lib/utils"
import { routeTree } from "./routeTree.gen"

OpenAPI.BASE = getApiBaseUrl()

const handleApiError = (error: Error) => {
  if (
    error instanceof ApiError &&
    [401, 403].includes(error.response?.status ?? -1)
  ) {
    clearSessionMarker()
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

const router = createRouter({ routeTree })
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router
  }
}

function AppContent() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
        <Toaster richColors closeButton />
      </QueryClientProvider>
    </ThemeProvider>
  )
}

async function bootstrap() {
  const didReload = await resetBrowserStateForDeployment(
    import.meta.env.VITE_APP_BUILD_ID ?? "",
  )

  if (didReload) {
    return
  }

  // Initialize all auth configs from consolidated endpoint (single API call)
  const consolidatedConfig = await loadConsolidatedAuthConfig()

  // Initialize auth modules with preloaded config
  await initEntra(consolidatedConfig.entra)
  await initGoogle(consolidatedConfig.google)
  await initGithub(consolidatedConfig.github)

  const googleClientId = isGoogleEnabled()
    ? consolidatedConfig.google.client_id || ""
    : null

  ReactDOM.createRoot(document.getElementById("root")!).render(
    <StrictMode>
      {googleClientId ? (
        <GoogleOAuthProvider clientId={googleClientId}>
          {isEntraEnabled() ? (
            <MsalProvider instance={getMsalInstance()}>
              <AppContent />
            </MsalProvider>
          ) : (
            <AppContent />
          )}
        </GoogleOAuthProvider>
      ) : isEntraEnabled() ? (
        <MsalProvider instance={getMsalInstance()}>
          <AppContent />
        </MsalProvider>
      ) : (
        <AppContent />
      )}
    </StrictMode>,
  )
}

await bootstrap()
