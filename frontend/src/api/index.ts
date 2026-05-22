import axios, { AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'

// API Response interface
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

// Token storage key
const ACCESS_TOKEN_KEY = 'access_token'

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Add auth token if available
    const token = localStorage.getItem(ACCESS_TOKEN_KEY)
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    const { code, message } = response.data
    
    // Check business logic errors
    if (code !== 200) {
      ElMessage.error(message || '请求失败')
      return Promise.reject(new Error(message))
    }
    
    return response.data
  },
  (error) => {
    // Handle HTTP errors
    const { response } = error
    
    if (response) {
      const { status, data } = response
      
      switch (status) {
        case 401:
          ElMessage.error('登录已过期，请重新登录')
          // Clear tokens and redirect to login
          localStorage.removeItem(ACCESS_TOKEN_KEY)
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user_info')
          // Use setTimeout to avoid issues during navigation
          setTimeout(() => {
            window.location.href = '/login'
          }, 100)
          break
        case 403:
          ElMessage.error(data?.message || '没有权限访问')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 422:
          // Validation error
          const errors = data?.errors
          if (Array.isArray(errors)) {
            const messages = errors.map((e: any) => `${e.field}: ${e.message}`).join('; ')
            ElMessage.error(messages || '数据验证失败')
          } else {
            ElMessage.error(data?.message || '数据验证失败')
          }
          break
        case 500:
          ElMessage.error(data?.message || '服务器内部错误')
          break
        default:
          ElMessage.error(data?.message || `请求失败: ${status}`)
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请稍后重试')
    } else {
      // 无 response：多为后端未启动或网络不可达
      ElMessage.error('无法连接服务器，请确认后端服务已启动 (默认 http://localhost:8000)')
    }
    
    return Promise.reject(error)
  }
)

export default api
