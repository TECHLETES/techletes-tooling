import { Bell, BellDot, CheckCheck, Trash2, X } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Separator } from "@/components/ui/separator"
import { type Notification, useNotifications } from "@/hooks/useNotifications"

const TYPE_COLOUR: Record<Notification["type"], string> = {
  info: "text-info",
  success: "text-success",
  warning: "text-warning",
  error: "text-destructive",
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  })
}

interface NotificationItemProps {
  notification: Notification
  onMarkRead: (id: string) => void
  onDismiss: (id: string) => void
}

function NotificationItem({
  notification,
  onMarkRead,
  onDismiss,
}: NotificationItemProps) {
  return (
    <button
      type="button"
      className={`w-full text-left flex cursor-pointer items-start gap-3 rounded-md px-3 py-2 transition-colors hover:bg-muted/50 ${
        notification.read ? "opacity-60" : ""
      }`}
      onClick={() => onMarkRead(notification.id)}
    >
      <span
        className={`mt-1 shrink-0 text-xs ${TYPE_COLOUR[notification.type]}`}
        aria-hidden
      >
        ●
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{notification.title}</p>
        <p className="truncate text-xs text-muted-foreground">
          {notification.message}
        </p>
        <p className="text-xs text-muted-foreground/60">
          {formatTime(notification.created_at)}
        </p>
      </div>
      <button
        className="ml-1 shrink-0 rounded text-muted-foreground hover:text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
        onClick={(e) => {
          e.stopPropagation()
          onDismiss(notification.id)
        }}
        aria-label="Dismiss notification"
        type="button"
      >
        <X className="h-3 w-3" />
      </button>
    </button>
  )
}

/**
 * Bell icon button that opens a dropdown listing real-time notifications.
 *
 * Uses the `useNotifications` hook internally — mount this once inside the
 * authenticated layout so the WebSocket connection is shared.
 */
export function NotificationBell() {
  const {
    notifications,
    unreadCount,
    isConnected,
    markAsRead,
    markAllAsRead,
    dismiss,
    clearAll,
  } = useNotifications()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative"
          aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ""}`}
        >
          {unreadCount > 0 ? (
            <BellDot className="h-5 w-5" />
          ) : (
            <Bell className="h-5 w-5" />
          )}
          {unreadCount > 0 && (
            <Badge
              variant="destructive"
              className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full px-1 text-[10px] leading-none"
            >
              {unreadCount > 99 ? "99+" : unreadCount}
            </Badge>
          )}
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-80">
        {/* Header */}
        <div className="flex items-center justify-between px-3 py-2">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold">Notifications</span>
            {!isConnected && (
              <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
                offline
              </span>
            )}
          </div>
          {notifications.length > 0 && (
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={markAllAsRead}
                title="Mark all as read"
              >
                <CheckCheck className="h-3.5 w-3.5" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={clearAll}
                title="Clear all"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            </div>
          )}
        </div>

        <Separator />

        {/* Notification list */}
        <div className="max-h-96 overflow-y-auto py-1">
          {notifications.length === 0 ? (
            <p className="px-3 py-6 text-center text-sm text-muted-foreground">
              No notifications
            </p>
          ) : (
            notifications.map((n) => (
              <NotificationItem
                key={n.id}
                notification={n}
                onMarkRead={markAsRead}
                onDismiss={dismiss}
              />
            ))
          )}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
