import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

function getRuntimeApiUrl(): string | undefined {
  if (typeof window === "undefined") {
    return undefined
  }

  return window.__APP_CONFIG__?.apiUrl?.trim()
}

export function getApiBaseUrl(): string {
  const configuredApiUrl = getRuntimeApiUrl()

  if (!configuredApiUrl && import.meta.env.DEV) {
    return window.location.origin
  }

  if (!configuredApiUrl) {
    throw new Error("Missing frontend runtime API configuration")
  }

  return new URL(configuredApiUrl).origin
}

export function getApiUrl(path: string): string {
  return new URL(path, `${getApiBaseUrl()}/`).toString()
}

export function getWebSocketUrl(path: string): string {
  const apiUrl = new URL(path, `${getApiBaseUrl()}/`)
  apiUrl.protocol = apiUrl.protocol === "https:" ? "wss:" : "ws:"
  return apiUrl.toString()
}
