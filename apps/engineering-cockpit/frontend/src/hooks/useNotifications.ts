import { useCallback, useEffect, useRef, useState } from "react"
import { hasSessionMarker } from "@/lib/session"
import { getWebSocketUrl } from "@/lib/utils"

export interface Notification {
  id: string
  type: "info" | "success" | "warning" | "error"
  title: string
  message: string
  created_at: string
  read: boolean
}

interface UseNotificationsReturn {
  notifications: Notification[]
  unreadCount: number
  isConnected: boolean
  markAsRead: (id: string) => void
  markAllAsRead: () => void
  dismiss: (id: string) => void
  clearAll: () => void
}

const MAX_NOTIFICATIONS = 50
const MAX_RECONNECT_DELAY_MS = 30_000

function buildWsUrl(): string {
  return getWebSocketUrl("/api/v1/notifications/ws")
}

/**
 * Manages a WebSocket connection to the notifications endpoint.
 *
 * The hook automatically reconnects with exponential back-off (1 s → 30 s)
 * when the connection drops.  Call it at the root of the authenticated layout
 * so the connection is shared across all pages.
 *
 * Example:
 * ```tsx
 * const { notifications, unreadCount } = useNotifications()
 * ```
 */
export function useNotifications(): UseNotificationsReturn {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [isConnected, setIsConnected] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const attemptRef = useRef(0)
  const isUnmountedRef = useRef(false)

  const connect = useCallback(() => {
    if (isUnmountedRef.current) return

    if (!hasSessionMarker()) return

    const ws = new WebSocket(buildWsUrl())
    wsRef.current = ws

    ws.onopen = () => {
      if (isUnmountedRef.current || wsRef.current !== ws) {
        ws.close()
        return
      }
      setIsConnected(true)
      attemptRef.current = 0
    }

    ws.onmessage = (event: MessageEvent<string>) => {
      try {
        const raw = JSON.parse(event.data) as Omit<Notification, "read">
        setNotifications((prev) =>
          [{ ...raw, read: false }, ...prev].slice(0, MAX_NOTIFICATIONS),
        )
      } catch {
        // ignore malformed frames
      }
    }

    ws.onclose = () => {
      // Only update state and reconnect if this is still the active socket
      if (wsRef.current === ws) {
        setIsConnected(false)
      }
      if (isUnmountedRef.current || wsRef.current !== ws) return
      // Exponential back-off reconnect
      const delay = Math.min(
        1_000 * 2 ** attemptRef.current,
        MAX_RECONNECT_DELAY_MS,
      )
      attemptRef.current += 1
      reconnectTimerRef.current = setTimeout(connect, delay)
    }

    ws.onerror = () => {
      // onerror is always followed by onclose, which triggers the reconnect
      ws.close()
    }
  }, [])

  useEffect(() => {
    isUnmountedRef.current = false
    connect()
    return () => {
      isUnmountedRef.current = true
      if (reconnectTimerRef.current !== null) {
        clearTimeout(reconnectTimerRef.current)
      }
      wsRef.current?.close()
    }
  }, [connect])

  const markAsRead = useCallback((id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n)),
    )
  }, [])

  const markAllAsRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
  }, [])

  const dismiss = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id))
  }, [])

  const clearAll = useCallback(() => {
    setNotifications([])
  }, [])

  const unreadCount = notifications.filter((n) => !n.read).length

  return {
    notifications,
    unreadCount,
    isConnected,
    markAsRead,
    markAllAsRead,
    dismiss,
    clearAll,
  }
}
