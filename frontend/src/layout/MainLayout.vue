<template>
  <el-container class="main-layout">
    <!-- Sidebar -->
    <el-aside :width="isCollapsed ? '64px' : '240px'" class="sidebar">
      <div class="logo-container" @click="router.push('/')">
        <div class="logo-icon">
          <el-icon :size="28"><Connection /></el-icon>
        </div>
        <transition name="fade">
          <span v-show="!isCollapsed" class="logo-text">DDPS</span>
        </transition>
      </div>
      
      <el-menu
        :default-active="currentRoute"
        :collapse="isCollapsed"
        :collapse-transition="false"
        router
        class="sidebar-menu"
      >
        <el-menu-item 
          v-for="item in filteredMenuItems" 
          :key="item.path" 
          :index="item.path"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.title }}</template>
        </el-menu-item>
      </el-menu>
      
      <div class="sidebar-footer">
        <el-button 
          :icon="isCollapsed ? 'Expand' : 'Fold'" 
          text 
          @click="isCollapsed = !isCollapsed"
          class="collapse-btn"
        />
      </div>
    </el-aside>

    <!-- Main Content -->
    <el-container class="main-container">
      <!-- Header -->
      <el-header class="header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentMeta.title">
              {{ currentMeta.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <el-tooltip content="系统状态" placement="bottom">
            <el-badge :is-dot="healthStatus === 'healthy'" class="status-badge">
              <el-button :icon="Monitor" circle text @click="checkHealth" />
            </el-badge>
          </el-tooltip>
          
          <el-dropdown trigger="click" @command="handleCommand">
            <div class="user-avatar">
              <el-avatar :size="32" class="avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <span class="username">{{ userStore.username || 'User' }}</span>
              <div class="user-roles" v-if="!isCollapsed">
                <el-tag 
                  v-if="userStore.isAdmin" 
                  type="danger" 
                  size="small"
                  effect="dark"
                >
                  管理员
                </el-tag>
              </div>
              <el-icon class="arrow"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item :icon="User" command="profile">个人信息</el-dropdown-item>
                <el-dropdown-item :icon="Setting" command="settings" v-if="userStore.isAdmin">
                  系统设置
                </el-dropdown-item>
                <el-dropdown-item divided :icon="SwitchButton" command="logout">
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- Content -->
      <el-main class="content">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, markRaw, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  Connection, Monitor, User, Setting, SwitchButton, ArrowDown,
  Odometer, Document, Share, Cpu, Box, DataAnalysis, UserFilled
} from '@element-plus/icons-vue'
import { healthApi } from '@/api/health'
import { useUserStore } from '@/store'
import { getAppSettings, setAppSettings } from '@/utils/settings'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isCollapsed = ref(getAppSettings().sidebarCollapsed)

watch(isCollapsed, (v) => {
  setAppSettings({ sidebarCollapsed: v })
})
const healthStatus = ref<'healthy' | 'degraded' | 'unknown'>('unknown')

interface MenuItem {
  path: string
  title: string
  icon: any
  roles?: string[]
}

const allMenuItems: MenuItem[] = [
  { path: '/dashboard', title: '工作台', icon: markRaw(Odometer) },
  { path: '/datasets', title: '数据管理', icon: markRaw(Document) },
  { path: '/graphs', title: '网络构建', icon: markRaw(Share) },
  { path: '/training', title: '模型训练', icon: markRaw(Cpu) },
  { path: '/prediction', title: '关联预测', icon: markRaw(Connection) },
  { path: '/models', title: '模型管理', icon: markRaw(Box) },
  { path: '/visualization', title: '可视化', icon: markRaw(DataAnalysis) },
  { path: '/users', title: '用户管理', icon: markRaw(UserFilled), roles: ['admin'] },
  { path: '/settings', title: '系统设置', icon: markRaw(Setting), roles: ['admin'] },
]

// Filter menu items based on user roles
const filteredMenuItems = computed(() => {
  return allMenuItems.filter(item => {
    // If no roles required, show to all
    if (!item.roles || item.roles.length === 0) return true
    
    // Superuser can see everything
    if (userStore.isSuperuser) return true
    
    // Check if user has any of the required roles
    return item.roles.some(role => userStore.hasRole(role))
  })
})

const currentRoute = computed(() => route.path)
const currentMeta = computed(() => route.meta as { title?: string })

const checkHealth = async () => {
  try {
    const response = await healthApi.check()
    healthStatus.value = response.data?.status === 'healthy' ? 'healthy' : 'degraded'
    ElMessage.success(`系统状态: ${response.data?.status || 'healthy'}`)
  } catch {
    healthStatus.value = 'degraded'
    ElMessage.error('无法连接到后端服务')
  }
}

const handleCommand = async (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      await userStore.logout()
      router.push('/login')
      break
  }
}

// Check health on mount
checkHealth()
</script>

<style lang="scss" scoped>
.main-layout {
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.95) 0%, rgba(15, 23, 42, 0.85) 100%);
  backdrop-filter: blur(20px);
  border-right: 1px solid var(--card-border);
  display: flex;
  flex-direction: column;
  transition: width var(--transition-normal);
  overflow: hidden;
}

.logo-container {
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  cursor: pointer;
  border-bottom: 1px solid var(--card-border);
  transition: all var(--transition-normal);
  
  &:hover {
    background: rgba(255, 255, 255, 0.03);
  }
  
  .logo-icon {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    flex-shrink: 0;
  }
  
  .logo-text {
    font-size: 20px;
    font-weight: 700;
    background: linear-gradient(135deg, var(--primary-light), var(--accent-color));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 2px;
  }
}

.sidebar-menu {
  flex: 1;
  padding: 16px 8px;
  overflow-y: auto;
  
  .el-menu-item {
    margin: 4px 0;
    border-radius: 8px;
    height: 48px;
    
    .el-icon {
      font-size: 18px;
    }
  }
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--card-border);
  
  .collapse-btn {
    width: 100%;
    color: var(--text-secondary);
    
    &:hover {
      color: var(--primary-light);
    }
  }
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header {
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--card-border);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  
  .status-badge {
    :deep(.el-badge__content.is-dot) {
      background-color: var(--success-color);
    }
  }
}

.user-avatar {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 8px;
  transition: background var(--transition-fast);
  
  &:hover {
    background: rgba(255, 255, 255, 0.05);
  }
  
  .avatar {
    background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
  }
  
  .username {
    color: var(--text-primary);
    font-weight: 500;
  }
  
  .user-roles {
    .el-tag {
      margin-left: 4px;
    }
  }
  
  .arrow {
    color: var(--text-secondary);
    font-size: 12px;
  }
}

.content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background: transparent;
}

// Transitions
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
</style>
