/**
 * Roles Service
 * Business logic wrapper around RBAC API client.
 * Handles role and permission management, data transformation, and error handling.
 */

import type {
  EntraAppRoleManifestPublic,
  PermissionPublic,
  PermissionsPublic,
  RoleCreate,
  RolePublic,
  RolesPublic,
  RoleUpdate,
} from "@/client"
import { RbacService as ApiRbacService } from "@/client"

export const RolesService = {
  /**
   * Fetch all roles with pagination.
   *
   * @param skip - Number of roles to skip (default: 0)
   * @param limit - Maximum roles to return (default: 10)
   * @returns Object with roles array, total count, and hasMore flag
   */
  async listRoles(skip: number = 0, limit: number = 10) {
    try {
      const response = (await ApiRbacService.listRoles({
        skip,
        limit,
      })) as RolesPublic

      return {
        roles: response.data || [],
        total: response.count || 0,
        hasMore: skip + limit < (response.count || 0),
      }
    } catch (_error) {
      throw new Error("Failed to fetch roles")
    }
  },

  /**
   * Get single role by ID.
   *
   * @param roleId - Role ID to fetch
   * @returns Role data or null if not found
   */
  async getRole(roleId: string): Promise<RolePublic | null> {
    try {
      const roles = (await ApiRbacService.listRoles({
        skip: 0,
        limit: 1000,
      })) as RolesPublic

      const role = roles.data?.find((r) => r.id === roleId) || null
      return role
    } catch (_error) {
      throw new Error(`Failed to fetch role ${roleId}`)
    }
  },

  /**
   * Create new role.
   *
   * @param data - Role creation data
   * @returns Created role
   */
  async createRole(data: RoleCreate): Promise<RolePublic> {
    try {
      const newRole = (await ApiRbacService.createRoleEndpoint({
        requestBody: data,
      })) as RolePublic

      return newRole
    } catch (_error) {
      throw new Error("Failed to create role")
    }
  },

  /**
   * Update existing role.
   *
   * @param roleId - Role ID to update
   * @param data - Partial role data to update
   * @returns Updated role
   */
  async updateRole(
    roleId: string,
    data: Partial<RoleUpdate>,
  ): Promise<RolePublic> {
    try {
      const updated = (await ApiRbacService.updateRoleEndpoint({
        roleId,
        requestBody: data,
      })) as RolePublic

      return updated
    } catch (_error) {
      throw new Error(`Failed to update role ${roleId}`)
    }
  },

  /**
   * Delete role.
   *
   * @param roleId - Role ID to delete
   * @returns Success status
   */
  async deleteRole(roleId: string): Promise<boolean> {
    try {
      await ApiRbacService.deleteRoleEndpoint({ roleId })
      return true
    } catch (_error) {
      throw new Error(`Failed to delete role ${roleId}`)
    }
  },

  /**
   * Fetch all permissions.
   *
   * @param skip - Number of permissions to skip (default: 0)
   * @param limit - Maximum permissions to return (default: 1000)
   * @returns Object with permissions array and total count
   */
  async listPermissions(skip: number = 0, limit: number = 1000) {
    try {
      const response = (await ApiRbacService.listPermissions({
        skip,
        limit,
      })) as PermissionsPublic

      return {
        permissions: response.data || [],
        total: response.count || 0,
      }
    } catch (_error) {
      throw new Error("Failed to fetch permissions")
    }
  },

  /**
   * Get user's roles for a specific user.
   *
   * @param userId - User ID
   * @returns Array of user's roles
   */
  async getUserRoles(userId: string): Promise<RolePublic[]> {
    try {
      const response = (await ApiRbacService.getUserRolesEndpoint({
        userId,
      })) as RolesPublic

      return response.data || []
    } catch (_error) {
      throw new Error(`Failed to fetch roles for user ${userId}`)
    }
  },

  /**
   * Get user's permissions for a specific user.
   *
   * @param userId - User ID
   * @returns Array of user's permissions
   */
  async getUserPermissions(userId: string): Promise<PermissionPublic[]> {
    try {
      const response = (await ApiRbacService.getUserPermissionsEndpoint({
        userId,
      })) as PermissionsPublic

      return response.data || []
    } catch (_error) {
      throw new Error(`Failed to fetch permissions for user ${userId}`)
    }
  },

  /**
   * Assign role to user.
   *
   * @param userId - User ID
   * @param roleId - Role ID to assign
   * @returns Success status
   */
  async assignRoleToUser(userId: string, roleId: string): Promise<boolean> {
    try {
      await ApiRbacService.assignRoleToUserEndpoint({
        userId,
        roleId,
      })
      return true
    } catch (_error) {
      throw new Error(`Failed to assign role to user ${userId}`)
    }
  },

  /**
   * Remove role from user.
   *
   * @param userId - User ID
   * @param roleId - Role ID to remove
   * @returns Success status
   */
  async removeRoleFromUser(userId: string, roleId: string): Promise<boolean> {
    try {
      await ApiRbacService.removeRoleFromUserEndpoint({
        userId,
        roleId,
      })
      return true
    } catch (_error) {
      throw new Error(`Failed to remove role from user ${userId}`)
    }
  },

  /**
   * Export the Entra application role manifest.
   *
   * @returns Entra app role manifest data
   */
  async getEntraManifest(): Promise<EntraAppRoleManifestPublic> {
    try {
      return ApiRbacService.getEntraManifest()
    } catch (_error) {
      throw new Error("Failed to export Entra app role manifest")
    }
  },
}
