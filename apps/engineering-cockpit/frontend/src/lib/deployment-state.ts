const BUILD_ID_STORAGE_KEY = "__fullstack_app_build_id__"

function getCookieNames(): string[] {
  return document.cookie
    .split(";")
    .map((cookie) => cookie.split("=")[0]?.trim())
    .filter((name): name is string => Boolean(name))
}

async function clearBrowserState(): Promise<void> {
  localStorage.clear()
  sessionStorage.clear()

  if ("caches" in window) {
    const cacheKeys = await caches.keys()
    await Promise.all(cacheKeys.map((cacheKey) => caches.delete(cacheKey)))
  }

  const serviceWorkerRegistrations =
    await navigator.serviceWorker?.getRegistrations()
  if (serviceWorkerRegistrations) {
    await Promise.all(
      serviceWorkerRegistrations.map((registration) =>
        registration.unregister(),
      ),
    )
  }

  // ponytail: best-effort cookie sweep for the current origin; HttpOnly cookies
  // cannot be removed from client code, so the server still owns those.
  for (const cookieName of getCookieNames()) {
    // biome-ignore lint/suspicious/noDocumentCookie: Clearing deployment cookies is intentional.
    document.cookie = `${cookieName}=;expires=${new Date(0).toUTCString()};path=/`
  }
}

export function shouldResetBrowserState(
  storedBuildId: string | null,
  currentBuildId: string,
): boolean {
  return storedBuildId !== currentBuildId
}

export async function resetBrowserStateForDeployment(
  currentBuildId: string,
): Promise<boolean> {
  const normalizedBuildId = currentBuildId.trim()

  if (!normalizedBuildId) {
    return false
  }

  let storedBuildId: string | null = null

  try {
    storedBuildId = localStorage.getItem(BUILD_ID_STORAGE_KEY)
  } catch {
    return false
  }

  if (!shouldResetBrowserState(storedBuildId, normalizedBuildId)) {
    return false
  }

  await clearBrowserState()

  try {
    localStorage.setItem(BUILD_ID_STORAGE_KEY, normalizedBuildId)
  } catch {
    return false
  }

  if (storedBuildId !== null) {
    window.location.reload()
    return true
  }

  return false
}
