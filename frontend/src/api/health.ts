import api, { ApiResponse } from './index'

export interface HealthStatus {
  status: 'healthy' | 'degraded'
  database?: string
  redis?: string
}

export const healthApi = {
  /**
   * Basic health check
   */
  check: (): Promise<ApiResponse<HealthStatus>> => {
    return api.get('/health')
  },

  /**
   * Full health check including database and redis
   */
  checkFull: (): Promise<ApiResponse<HealthStatus>> => {
    return api.get('/health/full')
  },

  /**
   * Database health check
   */
  checkDb: (): Promise<ApiResponse<HealthStatus>> => {
    return api.get('/health/db')
  },

  /**
   * Redis health check
   */
  checkRedis: (): Promise<ApiResponse<HealthStatus>> => {
    return api.get('/health/redis')
  },
}
