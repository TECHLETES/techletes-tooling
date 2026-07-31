/**
 * Notifications Service
 * Business logic wrapper around notification-related API endpoints.
 */

import type { Message } from "@/client"
import { NotificationsService as ApiNotificationsService } from "@/client"

export const NotificationsService = {
  /**
   * Send a test notification to all connected users.
   *
   * @returns Response message from the backend
   */
  async sendTestNotificationToAll(): Promise<Message> {
    try {
      return ApiNotificationsService.sendTestNotificationToAll()
    } catch (_error) {
      throw new Error("Failed to send test notification")
    }
  },
}
