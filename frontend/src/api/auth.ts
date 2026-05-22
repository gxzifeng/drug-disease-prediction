import api, { ApiResponse } from './index'

// ============ Types ============

export interface Token {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface UserInfo {
  id: number
  username: string
  email: string
  full_name: string | null
  is_active: boolean
  is_superuser: boolean
  roles: string[]
  created_at: string
  last_login: string | null
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  user: UserInfo
  token: Token
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  full_name?: string
}

export interface RegisterResponse {
  user: UserInfo
  message: string
}

export interface UserUpdateRequest {
  email?: string
  full_name?: string
}

export interface PasswordUpdateRequest {
  current_password: string
  new_password: string
}

export interface UserListItem {
  id: number
  username: string
  email: string
  full_name: string | null
  is_active: boolean
  is_superuser: boolean
  roles: string[]
  created_at: string
  last_login: string | null
}

export interface UserListResponse {
  items: UserListItem[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface UserAdminUpdateRequest {
  email?: string
  full_name?: string
  is_active?: boolean
  is_superuser?: boolean
  role_ids?: number[]
}

export interface UserCreateRequest {
  username: string
  email: string
  password: string
  full_name?: string
}

export interface Role {
  id: number
  name: string
  description: string | null
  permissions: string[] | null
  created_at: string
}

// ============ API Functions ============

export const authApi = {
  /**
   * Register a new user
   */
  register(data: RegisterRequest): Promise<ApiResponse<RegisterResponse>> {
    return api.post('/auth/register', data)
  },

  /**
   * Login with username and password
   */
  login(data: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    return api.post('/auth/login', data)
  },

  /**
   * Refresh access token
   */
  refreshToken(refreshToken: string): Promise<ApiResponse<Token>> {
    return api.post('/auth/refresh', { refresh_token: refreshToken })
  },

  /**
   * Logout (revoke refresh tokens)
   */
  logout(refreshToken?: string): Promise<ApiResponse<null>> {
    return api.post('/auth/logout', refreshToken ? { refresh_token: refreshToken } : {})
  },

  /**
   * Get current user info
   */
  getCurrentUser(): Promise<ApiResponse<UserInfo>> {
    return api.get('/auth/me')
  },

  /**
   * Update current user profile
   */
  updateProfile(data: UserUpdateRequest): Promise<ApiResponse<UserInfo>> {
    return api.put('/auth/me', data)
  },

  /**
   * Update current user password
   */
  updatePassword(data: PasswordUpdateRequest): Promise<ApiResponse<null>> {
    return api.put('/auth/me/password', data)
  },
}

export const userApi = {
  /**
   * List all users (Admin only)
   */
  listUsers(params: {
    page?: number
    page_size?: number
    is_active?: boolean
  } = {}): Promise<ApiResponse<UserListResponse>> {
    return api.get('/users', { params })
  },

  /**
   * Create a new user (Admin only)
   */
  createUser(data: UserCreateRequest, roles: string[] = ['user']): Promise<ApiResponse<UserInfo>> {
    return api.post('/users', data, { params: { roles } })
  },

  /**
   * Get user by ID (Admin only)
   */
  getUser(userId: number): Promise<ApiResponse<UserInfo>> {
    return api.get(`/users/${userId}`)
  },

  /**
   * Update user (Admin only)
   */
  updateUser(userId: number, data: UserAdminUpdateRequest): Promise<ApiResponse<UserInfo>> {
    return api.put(`/users/${userId}`, data)
  },

  /**
   * Delete user (Superuser only)
   */
  deleteUser(userId: number): Promise<ApiResponse<null>> {
    return api.delete(`/users/${userId}`)
  },

  /**
   * List all roles (Admin only)
   */
  listRoles(): Promise<ApiResponse<Role[]>> {
    return api.get('/users/roles/list')
  },
}

export default authApi
