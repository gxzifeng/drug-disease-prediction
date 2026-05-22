/**
 * 系统设置持久化（localStorage），供设置页与布局/训练等读取。
 */
const STORAGE_KEY = 'ddps_app_settings'

export interface AppSettings {
  language: string
  theme: string
  sidebarCollapsed: boolean
  randomSeed: number
  embeddingDim: number
  learningRate: number
}

const defaults: AppSettings = {
  language: 'zh-CN',
  theme: 'dark',
  sidebarCollapsed: false,
  randomSeed: 42,
  embeddingDim: 128,
  learningRate: 0.001,
}

export function getAppSettings(): AppSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { ...defaults }
    const parsed = JSON.parse(raw) as Partial<AppSettings>
    return { ...defaults, ...parsed }
  } catch {
    return { ...defaults }
  }
}

export function setAppSettings(partial: Partial<AppSettings>): void {
  const current = getAppSettings()
  const next = { ...current, ...partial }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
}
