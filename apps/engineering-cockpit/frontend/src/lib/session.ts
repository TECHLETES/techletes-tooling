const SESSION_MARKER_COOKIE = "session_present"

export function hasSessionMarker(): boolean {
  if (typeof document === "undefined") {
    return false
  }

  return document.cookie
    .split(";")
    .some((cookie) => cookie.trim() === `${SESSION_MARKER_COOKIE}=1`)
}

export function clearSessionMarker(): void {
  if (typeof document === "undefined") {
    return
  }

  // biome-ignore lint/suspicious/noDocumentCookie: non-sensitive session marker cookie
  document.cookie = `${SESSION_MARKER_COOKIE}=;expires=${new Date(0).toUTCString()};path=/`
}
