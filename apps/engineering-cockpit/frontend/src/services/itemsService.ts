/**
 * Items Service
 * Business logic wrapper around Items API client.
 * Handles data transformation, error handling, and API coordination.
 */

import type { ItemCreate, ItemPublic, ItemsPublic, ItemUpdate } from "@/client"
import { ItemsService as ApiItemsService } from "@/client"

export const ItemsService = {
  /**
   * Fetch all items with pagination.
   * Normalizes response into a standard format.
   *
   * @param skip - Number of items to skip (default: 0)
   * @param limit - Maximum items to return (default: 10)
   * @returns Object with items array, total count, and hasMore flag
   */
  async listItems(skip: number = 0, limit: number = 10) {
    try {
      const response = (await ApiItemsService.readItems({
        skip,
        limit,
      })) as ItemsPublic

      return {
        items: response.data || [],
        total: response.count || 0,
        hasMore: skip + limit < (response.count || 0),
      }
    } catch (_error) {
      throw new Error("Failed to fetch items")
    }
  },

  /**
   * Get single item by ID.
   *
   * @param itemId - Item ID to fetch
   * @returns Item data or null if not found
   */
  async getItem(itemId: string): Promise<ItemPublic | null> {
    try {
      const item = (await ApiItemsService.readItem({
        id: itemId,
      })) as ItemPublic

      if (!item) return null
      return item
    } catch (_error) {
      throw new Error(`Failed to fetch item ${itemId}`)
    }
  },

  /**
   * Create new item.
   *
   * @param data - Item creation data
   * @returns Created item
   */
  async createItem(data: ItemCreate): Promise<ItemPublic> {
    try {
      const newItem = (await ApiItemsService.createItem({
        requestBody: data,
      })) as ItemPublic

      return newItem
    } catch (_error) {
      throw new Error("Failed to create item")
    }
  },

  /**
   * Update existing item.
   *
   * @param itemId - Item ID to update
   * @param data - Partial item data to update
   * @returns Updated item
   */
  async updateItem(
    itemId: string,
    data: Partial<ItemUpdate>,
  ): Promise<ItemPublic> {
    try {
      const updated = (await ApiItemsService.updateItem({
        id: itemId,
        requestBody: data,
      })) as ItemPublic

      return updated
    } catch (_error) {
      throw new Error(`Failed to update item ${itemId}`)
    }
  },

  /**
   * Delete item.
   *
   * @param itemId - Item ID to delete
   * @returns Success status
   */
  async deleteItem(itemId: string): Promise<boolean> {
    try {
      await ApiItemsService.deleteItem({ id: itemId })
      return true
    } catch (_error) {
      throw new Error(`Failed to delete item ${itemId}`)
    }
  },

  /**
   * Batch delete multiple items.
   *
   * @param itemIds - Array of item IDs to delete
   * @returns Object with success and failure counts
   */
  async batchDelete(itemIds: string[]) {
    const results = await Promise.allSettled(
      itemIds.map((id) => ItemsService.deleteItem(id)),
    )
    return {
      succeeded: results.filter((r) => r.status === "fulfilled").length,
      failed: results.filter((r) => r.status === "rejected").length,
    }
  },
}
