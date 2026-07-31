import { AxiosError } from "axios"

import { client } from "./generated/client.gen"
import {
  AdminService as GeneratedAdminService,
  AuthConfigService as GeneratedAuthConfigService,
  AuthEntraService as GeneratedAuthEntraService,
  AuthGithubService as GeneratedAuthGithubService,
  AuthGoogleService as GeneratedAuthGoogleService,
  FilesService,
  ItemsService as GeneratedItemsService,
  LoginService as GeneratedLoginService,
  NotificationsService as GeneratedNotificationsService,
  PrivateService as GeneratedPrivateService,
  RbacService as GeneratedRbacService,
  TasksService as GeneratedTasksService,
  TenantsService,
  UsersService as GeneratedUsersService,
  UtilsService as GeneratedUtilsService,
} from "./generated"
import type {
  AppConfig,
  BodyLoginLoginAccessToken,
  ConsolidatedAuthConfig,
  EntraAppRoleManifestPublic,
  EntraLoginRequest,
  EntraProviderConfig,
  ItemCreate,
  ItemPublic,
  ItemUpdate,
  ItemsPublic,
  JobsListResponse,
  JobsStatsResponse,
  Message,
  NewPassword,
  PermissionsPublic,
  PrivateUserCreate,
  RoleCreate,
  RolePublic,
  RolesPublic,
  RoleUpdate,
  TaskCreate,
  TaskPublic,
  GitHubExchangeCodeRequest,
  GitHubLoginRequest,
  GitHubProviderConfig,
  GoogleLoginRequest,
  GoogleProviderConfig,
  Token,
  UpdatePassword,
  UserCreate,
  UserPublic,
  UserRegister,
  UsersPublic,
  UserUpdate,
  UserUpdateMe,
} from "./generated"

export type * from "./generated"
export { AxiosError as ApiError, client }
export { FilesService, TenantsService }

export type Body_login_login_access_token = BodyLoginLoginAccessToken

type TokenResolver = (() => Promise<string> | string) | undefined

let tokenResolver: TokenResolver

client.setConfig({ throwOnError: true, withCredentials: true })

async function unwrapData<T>(request: Promise<unknown>): Promise<T> {
  const response = (await request) as { data: T }
  return response.data
}

export const AdminService = {
  getJobsStats: () =>
    unwrapData<JobsStatsResponse>(GeneratedAdminService.getApiV1AdminJobsStats()),
  getJobsList: (query?: Record<string, unknown>) =>
    unwrapData<JobsListResponse>(
      GeneratedAdminService.getApiV1AdminJobsList({ query }),
    ),
}

export const PrivateService = {
  createUser: ({ requestBody }: { requestBody: PrivateUserCreate }) =>
    unwrapData<UserPublic>(
      GeneratedPrivateService.postApiV1PrivateUsers({ body: requestBody }),
    ),
}

export const OpenAPI = {
  get BASE(): string {
    return client.getConfig().baseURL ?? ""
  },
  set BASE(value: string) {
    client.setConfig({ baseURL: value })
  },
  get TOKEN(): TokenResolver {
    return tokenResolver
  },
  set TOKEN(value: TokenResolver) {
    tokenResolver = value
    client.setConfig({
      auth: async () => {
        if (!tokenResolver) {
          return undefined
        }

        const token = await tokenResolver()
        return token || undefined
      },
    })
  },
}

export const LoginService = {
  loginAccessToken: ({ formData }: { formData: BodyLoginLoginAccessToken }) =>
    unwrapData<Token>(
      GeneratedLoginService.postApiV1LoginAccessToken({ body: formData }),
    ),
  recoverPassword: ({ email }: { email: string }) =>
    unwrapData<Message>(
      GeneratedLoginService.postApiV1PasswordRecoveryByEmail({
        path: { email },
      }),
    ),
  resetPassword: ({ requestBody }: { requestBody: NewPassword }) =>
    unwrapData<Message>(
      GeneratedLoginService.postApiV1ResetPassword({ body: requestBody }),
    ),
}

export const UsersService = {
  readUsers: (query?: { skip?: number; limit?: number }) =>
    unwrapData<UsersPublic>(GeneratedUsersService.getApiV1Users({ query })),
  createUser: ({ requestBody }: { requestBody: UserCreate }) =>
    unwrapData<UserPublic>(
      GeneratedUsersService.postApiV1Users({ body: requestBody }),
    ),
  deleteUserMe: () =>
    unwrapData<Message>(GeneratedUsersService.deleteApiV1UsersMe()),
  readUserMe: () =>
    unwrapData<UserPublic>(GeneratedUsersService.getApiV1UsersMe()),
  updateUserMe: ({ requestBody }: { requestBody: UserUpdateMe }) =>
    unwrapData<UserPublic>(
      GeneratedUsersService.patchApiV1UsersMe({ body: requestBody }),
    ),
  updatePasswordMe: ({ requestBody }: { requestBody: UpdatePassword }) =>
    unwrapData<Message>(
      GeneratedUsersService.patchApiV1UsersMePassword({ body: requestBody }),
    ),
  registerUser: ({ requestBody }: { requestBody: UserRegister }) =>
    unwrapData<UserPublic>(
      GeneratedUsersService.postApiV1UsersSignup({ body: requestBody }),
    ),
  deleteUser: ({ userId }: { userId: string }) =>
    unwrapData<Message>(
      GeneratedUsersService.deleteApiV1UsersByUserId({
        path: { user_id: userId },
      }),
    ),
  readUser: ({ userId }: { userId: string }) =>
    unwrapData<UserPublic>(
      GeneratedUsersService.getApiV1UsersByUserId({
        path: { user_id: userId },
      }),
    ),
  updateUser: ({
    userId,
    requestBody,
  }: {
    userId: string
    requestBody: UserUpdate
  }) =>
    unwrapData<UserPublic>(
      GeneratedUsersService.patchApiV1UsersByUserId({
        body: requestBody,
        path: { user_id: userId },
      }),
    ),
}

export const UtilsService = {
  getAppConfig: () =>
    unwrapData<AppConfig>(GeneratedUtilsService.getApiV1UtilsConfig()),
}

export const ItemsService = {
  readItems: (query?: { skip?: number; limit?: number }) =>
    unwrapData<ItemsPublic>(GeneratedItemsService.getApiV1Items({ query })),
  createItem: ({ requestBody }: { requestBody: ItemCreate }) =>
    unwrapData<ItemPublic>(
      GeneratedItemsService.postApiV1Items({ body: requestBody }),
    ),
  deleteItem: ({ id }: { id: string }) =>
    unwrapData<Message>(GeneratedItemsService.deleteApiV1ItemsById({ path: { id } })),
  readItem: ({ id }: { id: string }) =>
    unwrapData<ItemPublic>(GeneratedItemsService.getApiV1ItemsById({ path: { id } })),
  updateItem: ({
    id,
    requestBody,
  }: {
    id: string
    requestBody: ItemUpdate
  }) =>
    unwrapData<ItemPublic>(
      GeneratedItemsService.putApiV1ItemsById({
        body: requestBody,
        path: { id },
      }),
    ),
}

export const RbacService = {
  listPermissions: (query?: { skip?: number; limit?: number }) =>
    unwrapData<PermissionsPublic>(
      GeneratedRbacService.getApiV1RbacPermissions({ query }),
    ),
  listRoles: (query?: { skip?: number; limit?: number }) =>
    unwrapData<RolesPublic>(GeneratedRbacService.getApiV1RbacRoles({ query })),
  createRoleEndpoint: ({ requestBody }: { requestBody: RoleCreate }) =>
    unwrapData<RolePublic>(
      GeneratedRbacService.postApiV1RbacRoles({ body: requestBody }),
    ),
  updateRoleEndpoint: ({
    roleId,
    requestBody,
  }: {
    roleId: string
    requestBody: RoleUpdate
  }) =>
    unwrapData<RolePublic>(
      GeneratedRbacService.patchApiV1RbacRolesByRoleId({
        body: requestBody,
        path: { role_id: roleId },
      }),
    ),
  deleteRoleEndpoint: ({ roleId }: { roleId: string }) =>
    unwrapData<Message>(
      GeneratedRbacService.deleteApiV1RbacRolesByRoleId({
        path: { role_id: roleId },
      }),
    ),
  getUserRolesEndpoint: ({ userId }: { userId: string }) =>
    unwrapData<RolesPublic>(
      GeneratedRbacService.getApiV1RbacUsersByUserIdRoles({
        path: { user_id: userId },
      }),
    ),
  getUserPermissionsEndpoint: ({ userId }: { userId: string }) =>
    unwrapData<PermissionsPublic>(
      GeneratedRbacService.getApiV1RbacUsersByUserIdPermissions({
        path: { user_id: userId },
      }),
    ),
  assignRoleToUserEndpoint: ({
    userId,
    roleId,
  }: {
    userId: string
    roleId: string
  }) =>
    unwrapData<Message>(
      GeneratedRbacService.postApiV1RbacUsersByUserIdRolesByRoleId({
        path: { role_id: roleId, user_id: userId },
      }),
    ),
  removeRoleFromUserEndpoint: ({
    userId,
    roleId,
  }: {
    userId: string
    roleId: string
  }) =>
    unwrapData<Message>(
      GeneratedRbacService.deleteApiV1RbacUsersByUserIdRolesByRoleId({
        path: { role_id: roleId, user_id: userId },
      }),
    ),
  getEntraManifest: () =>
    unwrapData<EntraAppRoleManifestPublic>(
      GeneratedRbacService.getApiV1RbacRolesEntraManifest(),
    ),
}

export const NotificationsService = {
  sendTestNotificationToAll: () =>
    unwrapData<Message>(
      GeneratedNotificationsService.postApiV1NotificationsSendTestAll(),
    ),
}

export const TasksService = {
  enqueueTask: ({ requestBody }: { requestBody: TaskCreate }) =>
    unwrapData<TaskPublic>(
      GeneratedTasksService.postApiV1TasksEnqueue({ body: requestBody }),
    ),
}

export const AuthConfigService = {
  getApiV1AuthConfig: () =>
    unwrapData<ConsolidatedAuthConfig>(
      GeneratedAuthConfigService.getApiV1AuthConfig(),
    ),
}

export const AuthGithubService = {
  getApiV1AuthGithubConfig: () =>
    unwrapData<GitHubProviderConfig>(
      GeneratedAuthGithubService.getApiV1AuthGithubConfig(),
    ),
  postApiV1AuthGithubLogin: ({ body }: { body: GitHubLoginRequest }) =>
    unwrapData<Token>(GeneratedAuthGithubService.postApiV1AuthGithubLogin({ body })),
  postApiV1AuthGithubExchangeCode: ({ body }: { body: GitHubExchangeCodeRequest }) =>
    unwrapData<Token>(
      GeneratedAuthGithubService.postApiV1AuthGithubExchangeCode({ body }),
    ),
}

export const AuthGoogleService = {
  getApiV1AuthGoogleConfig: () =>
    unwrapData<GoogleProviderConfig>(
      GeneratedAuthGoogleService.getApiV1AuthGoogleConfig(),
    ),
  postApiV1AuthGoogleLogin: ({ body }: { body: GoogleLoginRequest }) =>
    unwrapData<Token>(GeneratedAuthGoogleService.postApiV1AuthGoogleLogin({ body })),
}

export const AuthEntraService = {
  getApiV1AuthEntraConfig: () =>
    unwrapData<EntraProviderConfig>(
      GeneratedAuthEntraService.getApiV1AuthEntraConfig(),
    ),
  postApiV1AuthEntraLogin: ({ body }: { body: EntraLoginRequest }) =>
    unwrapData<Token>(GeneratedAuthEntraService.postApiV1AuthEntraLogin({ body })),
}
