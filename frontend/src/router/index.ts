import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/store'
import { ElMessage } from 'element-plus'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { title: '登录', requiresAuth: false, guestOnly: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/Register.vue'),
    meta: { title: '注册', requiresAuth: false, guestOnly: true }
  },
  {
    path: '/',
    component: () => import('@/layout/MainLayout.vue'),
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Dashboard.vue'),
        meta: { title: '工作台', icon: 'Odometer' }
      },
      {
        path: 'datasets',
        name: 'Datasets',
        component: () => import('@/views/datasets/DatasetList.vue'),
        meta: { title: '数据管理', icon: 'Document' }
      },
      {
        path: 'graphs',
        name: 'Graphs',
        component: () => import('@/views/graphs/GraphList.vue'),
        meta: { title: '网络构建', icon: 'Share' }
      },
      {
        path: 'training',
        name: 'Training',
        component: () => import('@/views/training/TrainingList.vue'),
        meta: { title: '表示学习', icon: 'Cpu' }
      },
      {
        path: 'experiments',
        name: 'Experiments',
        component: () => import('@/views/experiments/ExperimentList.vue'),
        meta: { title: '分类器实验', icon: 'DataLine' }
      },
      {
        path: 'prediction',
        name: 'Prediction',
        component: () => import('@/views/prediction/Prediction.vue'),
        meta: { title: '关联预测', icon: 'Connection' }
      },
      {
        path: 'models',
        name: 'Models',
        component: () => import('@/views/models/ModelList.vue'),
        meta: { title: '模型管理', icon: 'Box' }
      },
      {
        path: 'visualization',
        name: 'Visualization',
        component: () => import('@/views/visualization/NetworkViz.vue'),
        meta: { title: '可视化', icon: 'DataAnalysis' }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/auth/Profile.vue'),
        meta: { title: '个人信息', icon: 'User', hidden: true }
      },
      {
        path: 'users',
        name: 'UserManagement',
        component: () => import('@/views/admin/UserManagement.vue'),
        meta: { title: '用户管理', icon: 'UserFilled', roles: ['admin'] }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/settings/Settings.vue'),
        meta: { title: '系统设置', icon: 'Setting', roles: ['admin'] }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/NotFound.vue'),
    meta: { title: '页面未找到', requiresAuth: false }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
router.beforeEach(async (to, from, next) => {
  // Set page title
  document.title = `${to.meta.title || '药物-疾病预测系统'} - DDPS`
  
  const userStore = useUserStore()
  const isLoggedIn = userStore.isLoggedIn
  const requiresAuth = to.meta.requiresAuth !== false
  const guestOnly = to.meta.guestOnly === true
  const requiredRoles = to.meta.roles as string[] | undefined
  
  // Guest only pages (login, register) - redirect to dashboard if logged in
  if (guestOnly && isLoggedIn) {
    return next('/dashboard')
  }
  
  // Protected pages - redirect to login if not logged in
  if (requiresAuth && !isLoggedIn) {
    ElMessage.warning('请先登录')
    return next({
      path: '/login',
      query: { redirect: to.fullPath }
    })
  }
  
  // Check role-based access
  if (requiredRoles && requiredRoles.length > 0 && isLoggedIn) {
    const hasRequiredRole = requiredRoles.some(role => userStore.hasRole(role)) || userStore.isSuperuser
    if (!hasRequiredRole) {
      ElMessage.error('没有权限访问此页面')
      return next('/dashboard')
    }
  }
  
  // Fetch user info if logged in but no user info
  if (isLoggedIn && !userStore.userInfo) {
    await userStore.fetchUserInfo()
  }
  
  next()
})

export default router

// Export route types for menu generation
export interface RouteMetaConfig {
  title?: string
  icon?: string
  roles?: string[]
  hidden?: boolean
  requiresAuth?: boolean
}

// Helper function to filter routes by role
export function getAccessibleRoutes(routes: RouteRecordRaw[], userRoles: string[], isSuperuser: boolean): RouteRecordRaw[] {
  return routes.filter(route => {
    const meta = route.meta as RouteMetaConfig | undefined
    
    // Filter out hidden routes
    if (meta?.hidden) return false
    
    // Check role requirement
    if (meta?.roles && meta.roles.length > 0) {
      if (isSuperuser) return true
      return meta.roles.some(role => userRoles.includes(role))
    }
    
    return true
  })
}
