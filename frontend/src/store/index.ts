import { defineStore } from 'pinia'
import { authApi, UserInfo } from '@/api/auth'
import { ElMessage } from 'element-plus'

// Token storage keys
const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const USER_INFO_KEY = 'user_info'

// User store
export const useUserStore = defineStore('user', {
  state: () => ({
    accessToken: localStorage.getItem(ACCESS_TOKEN_KEY) || '',
    refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY) || '',
    userInfo: JSON.parse(localStorage.getItem(USER_INFO_KEY) || 'null') as UserInfo | null,
    loading: false,
  }),
  
  getters: {
    isLoggedIn: (state) => !!state.accessToken,
    isAdmin: (state) => state.userInfo?.roles?.includes('admin') || state.userInfo?.is_superuser || false,
    isSuperuser: (state) => state.userInfo?.is_superuser || false,
    username: (state) => state.userInfo?.username || '',
    roles: (state) => state.userInfo?.roles || [],
    hasRole: (state) => (role: string) => state.userInfo?.roles?.includes(role) || state.userInfo?.is_superuser || false,
  },
  
  actions: {
    // Set tokens
    setTokens(accessToken: string, refreshToken: string) {
      this.accessToken = accessToken
      this.refreshToken = refreshToken
      localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
      localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
    },
    
    // Set user info
    setUserInfo(info: UserInfo | null) {
      this.userInfo = info
      if (info) {
        localStorage.setItem(USER_INFO_KEY, JSON.stringify(info))
      } else {
        localStorage.removeItem(USER_INFO_KEY)
      }
    },
    
    // Login action
    async login(username: string, password: string) {
      this.loading = true
      try {
        const response = await authApi.login({ username, password })
        const { user, token } = response.data
        
        this.setTokens(token.access_token, token.refresh_token)
        this.setUserInfo(user)
        
        return { success: true, user }
      } catch (error: any) {
        console.error('Login failed:', error)
        throw error
      } finally {
        this.loading = false
      }
    },
    
    // Register action
    async register(data: { username: string; email: string; password: string; full_name?: string }) {
      this.loading = true
      try {
        const response = await authApi.register(data)
        return { success: true, user: response.data.user }
      } catch (error: any) {
        console.error('Registration failed:', error)
        throw error
      } finally {
        this.loading = false
      }
    },
    
    // Logout action
    async logout(silent: boolean = false) {
      try {
        if (this.refreshToken) {
          await authApi.logout(this.refreshToken)
        }
      } catch (error) {
        console.error('Logout API failed:', error)
      } finally {
        this.clearAuth()
        if (!silent) {
          ElMessage.success('已退出登录')
        }
      }
    },
    
    // Clear auth state
    clearAuth() {
      this.accessToken = ''
      this.refreshToken = ''
      this.userInfo = null
      localStorage.removeItem(ACCESS_TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
      localStorage.removeItem(USER_INFO_KEY)
    },
    
    // Refresh token action
    async refreshAccessToken() {
      if (!this.refreshToken) {
        throw new Error('No refresh token available')
      }
      
      try {
        const response = await authApi.refreshToken(this.refreshToken)
        const token = response.data
        
        this.setTokens(token.access_token, token.refresh_token)
        return token.access_token
      } catch (error) {
        console.error('Token refresh failed:', error)
        this.clearAuth()
        throw error
      }
    },
    
    // Fetch current user info
    async fetchUserInfo() {
      if (!this.accessToken) return null
      
      try {
        const response = await authApi.getCurrentUser()
        this.setUserInfo(response.data)
        return response.data
      } catch (error) {
        console.error('Failed to fetch user info:', error)
        return null
      }
    },
    
    // Update user profile
    async updateProfile(data: { email?: string; full_name?: string }) {
      try {
        const response = await authApi.updateProfile(data)
        this.setUserInfo(response.data)
        ElMessage.success('个人信息更新成功')
        return response.data
      } catch (error) {
        console.error('Failed to update profile:', error)
        throw error
      }
    },
    
    // Update password
    async updatePassword(currentPassword: string, newPassword: string) {
      try {
        await authApi.updatePassword({
          current_password: currentPassword,
          new_password: newPassword,
        })
        ElMessage.success('密码更新成功')
        return true
      } catch (error) {
        console.error('Failed to update password:', error)
        throw error
      }
    },
    
    // Check if token needs refresh
    isTokenExpiringSoon() {
      // Simple check - in production, decode JWT and check exp
      return false
    },
  },
})

// App store for global state
export const useAppStore = defineStore('app', {
  state: () => ({
    loading: false,
    sidebarCollapsed: false,
    menuItems: [] as Array<{ path: string; title: string; icon: string; roles?: string[] }>,
  }),
  
  actions: {
    setLoading(value: boolean) {
      this.loading = value
    },
    
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
    },
  },
})
