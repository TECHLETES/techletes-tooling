/**
 * Users Service
 * Business logic wrapper around Users API client.
 * Handles user management, data transformation, and error handling.
 */

import type {
  Message,
  UpdatePassword,
  UserCreate,
  UserPublic,
  UserRegister,
  UsersPublic,
  UserUpdate,
  UserUpdateMe,
} from "@/client"
import { UsersService as ApiUsersService } from "@/client"
import { UsersService as GeneratedUsersService } from "@/client/generated/sdk.gen"
import { getApiUrl } from "@/lib/utils"

export const UsersService = {
  /**
   * Fetch all users with pagination.
   *
   * @param skip - Number of users to skip (default: 0)
   * @param limit - Maximum users to return (default: 10)
   * @returns Object with users array, total count, and hasMore flag
   */
  async listUsers(skip: number = 0, limit: number = 10) {
    try {
      const response = (await ApiUsersService.readUsers({
        skip,
        limit,
      })) as UsersPublic

      return {
        users: response.data || [],
        total: response.count || 0,
        hasMore: skip + limit < (response.count || 0),
      }
    } catch (_error) {
      throw new Error("Failed to fetch users")
    }
  },

  /**
   * Get current authenticated user.
   *
   * @returns Current user data
   */
  async getCurrentUser(): Promise<UserPublic> {
    try {
      const user = (await ApiUsersService.readUserMe()) as UserPublic
      return user
    } catch (_error) {
      throw new Error("Failed to fetch current user")
    }
  },

  /**
   * Get single user by ID.
   *
   * @param userId - User ID to fetch
   * @returns User data or null if not found
   */
  async getUser(userId: string): Promise<UserPublic | null> {
    try {
      const user = (await ApiUsersService.readUser({
        userId,
      })) as UserPublic

      if (!user) return null
      return user
    } catch (_error) {
      throw new Error(`Failed to fetch user ${userId}`)
    }
  },

  /**
   * Create new user (admin only).
   *
   * @param data - User creation data
   * @returns Created user
   */
  async createUser(data: UserCreate): Promise<UserPublic> {
    try {
      const newUser = (await ApiUsersService.createUser({
        requestBody: data,
      })) as UserPublic

      return newUser
    } catch (_error) {
      throw new Error("Failed to create user")
    }
  },

  /**
   * Update user (admin only).
   *
   * @param userId - User ID to update
   * @param data - Partial user data to update
   * @returns Updated user
   */
  async updateUser(
    userId: string,
    data: Partial<UserUpdate>,
  ): Promise<UserPublic> {
    try {
      const updated = (await ApiUsersService.updateUser({
        userId,
        requestBody: data,
      })) as UserPublic

      return updated
    } catch (_error) {
      throw new Error(`Failed to update user ${userId}`)
    }
  },

  /**
   * Update current user's own information.
   *
   * @param data - Partial user data to update
   * @returns Updated user
   */
  async updateCurrentUser(data: Partial<UserUpdateMe>): Promise<UserPublic> {
    try {
      const updated = (await ApiUsersService.updateUserMe({
        requestBody: data,
      })) as UserPublic

      return updated
    } catch (_error) {
      throw new Error("Failed to update user information")
    }
  },

  /**
   * Register a new user via the public signup flow.
   *
   * @param data - Registration data
   * @returns Created user
   */
  async registerUser(data: UserRegister): Promise<UserPublic> {
    try {
      const newUser = (await ApiUsersService.registerUser({
        requestBody: data,
      })) as UserPublic

      return newUser
    } catch (_error) {
      throw new Error("Failed to register user")
    }
  },

  /**
   * Update the current user's password.
   *
   * @param data - Password update payload
   */
  async updatePasswordMe(data: UpdatePassword): Promise<Message> {
    try {
      return ApiUsersService.updatePasswordMe({ requestBody: data })
    } catch (_error) {
      throw new Error("Failed to update password")
    }
  },

  /**
   * Delete the current authenticated user.
   */
  async deleteCurrentUser(): Promise<Message> {
    try {
      return ApiUsersService.deleteUserMe()
    } catch (_error) {
      throw new Error("Failed to delete current user")
    }
  },

  /**
   * Delete user (admin only).
   *
   * @param userId - User ID to delete
   * @returns Success status
   */
  async deleteUser(userId: string): Promise<boolean> {
    try {
      await ApiUsersService.deleteUser({ userId })
      return true
    } catch (_error) {
      throw new Error(`Failed to delete user ${userId}`)
    }
  },

  /**
   * Batch delete multiple users (admin only).
   *
   * @param userIds - Array of user IDs to delete
   * @returns Object with success and failure counts
   */
  async batchDelete(userIds: string[]) {
    const results = await Promise.allSettled(
      userIds.map((id) => UsersService.deleteUser(id)),
    )
    return {
      succeeded: results.filter((r) => r.status === "fulfilled").length,
      failed: results.filter((r) => r.status === "rejected").length,
    }
  },

  /**
   * Upload an avatar image for the current user.
   *
   * @param file - The image file to upload (JPEG or PNG, max 5 MB)
   * @returns Updated user data
   */
  async uploadAvatar(file: File): Promise<UserPublic> {
    try {
      const response = (await GeneratedUsersService.postApiV1UsersMeAvatar({
        body: { file },
      })) as unknown as { data: UserPublic }
      return response.data
    } catch (_error) {
      throw new Error("Failed to upload avatar")
    }
  },

  /**
   * Delete the current user's avatar image.
   *
   * @returns Updated user data
   */
  async deleteAvatar(): Promise<UserPublic> {
    try {
      const response =
        (await GeneratedUsersService.deleteApiV1UsersMeAvatar()) as unknown as {
          data: UserPublic
        }
      return response.data
    } catch (_error) {
      throw new Error("Failed to delete avatar")
    }
  },

  getCurrentUserAvatarDownloadUrl(): string {
    return getApiUrl("/api/v1/users/me/avatar/download")
  },
}
