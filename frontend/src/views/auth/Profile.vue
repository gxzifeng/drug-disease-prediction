<template>
  <div class="profile-page">
    <el-row :gutter="24">
      <!-- User Info Card -->
      <el-col :xs="24" :lg="8">
        <el-card class="profile-card">
          <div class="user-header">
            <el-avatar :size="100" class="user-avatar">
              <el-icon :size="50"><User /></el-icon>
            </el-avatar>
            <h2>{{ userInfo?.username }}</h2>
            <p class="user-email">{{ userInfo?.email }}</p>
            <div class="user-roles">
              <el-tag
                v-for="role in userInfo?.roles"
                :key="role"
                :type="role === 'admin' ? 'danger' : 'primary'"
                size="small"
              >
                {{ role === 'admin' ? '管理员' : '普通用户' }}
              </el-tag>
              <el-tag v-if="userInfo?.is_superuser" type="warning" size="small">
                超级管理员
              </el-tag>
            </div>
          </div>
          
          <el-divider />
          
          <div class="user-info-list">
            <div class="info-item">
              <span class="label">姓名</span>
              <span class="value">{{ userInfo?.full_name || '未设置' }}</span>
            </div>
            <div class="info-item">
              <span class="label">注册时间</span>
              <span class="value">{{ formatDate(userInfo?.created_at) }}</span>
            </div>
            <div class="info-item">
              <span class="label">最后登录</span>
              <span class="value">{{ formatDate(userInfo?.last_login) || '首次登录' }}</span>
            </div>
            <div class="info-item">
              <span class="label">账号状态</span>
              <el-tag :type="userInfo?.is_active ? 'success' : 'danger'" size="small">
                {{ userInfo?.is_active ? '正常' : '已禁用' }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <!-- Edit Forms -->
      <el-col :xs="24" :lg="16">
        <!-- Profile Edit -->
        <el-card class="edit-card">
          <template #header>
            <div class="card-header">
              <span>编辑个人信息</span>
            </div>
          </template>
          
          <el-form
            ref="profileFormRef"
            :model="profileForm"
            :rules="profileRules"
            label-width="100px"
          >
            <el-form-item label="用户名">
              <el-input v-model="userInfo.username" disabled />
            </el-form-item>
            
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="profileForm.email" placeholder="请输入邮箱" />
            </el-form-item>
            
            <el-form-item label="姓名" prop="full_name">
              <el-input v-model="profileForm.full_name" placeholder="请输入姓名" />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" :loading="profileLoading" @click="handleUpdateProfile">
                保存修改
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
        
        <!-- Password Change -->
        <el-card class="edit-card" style="margin-top: 24px;">
          <template #header>
            <div class="card-header">
              <span>修改密码</span>
            </div>
          </template>
          
          <el-form
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordRules"
            label-width="100px"
          >
            <el-form-item label="当前密码" prop="current_password">
              <el-input
                v-model="passwordForm.current_password"
                type="password"
                placeholder="请输入当前密码"
                show-password
              />
            </el-form-item>
            
            <el-form-item label="新密码" prop="new_password">
              <el-input
                v-model="passwordForm.new_password"
                type="password"
                placeholder="请输入新密码"
                show-password
              />
            </el-form-item>
            
            <el-form-item label="确认密码" prop="confirm_password">
              <el-input
                v-model="passwordForm.confirm_password"
                type="password"
                placeholder="请再次输入新密码"
                show-password
              />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" :loading="passwordLoading" @click="handleUpdatePassword">
                修改密码
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { FormInstance, FormRules, ElMessage } from 'element-plus'
import { User } from '@element-plus/icons-vue'
import { useUserStore } from '@/store'
import dayjs from 'dayjs'

const userStore = useUserStore()

const profileFormRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()
const profileLoading = ref(false)
const passwordLoading = ref(false)

const userInfo = computed(() => userStore.userInfo)

const profileForm = reactive({
  email: userStore.userInfo?.email || '',
  full_name: userStore.userInfo?.full_name || '',
})

const passwordForm = reactive({
  current_password: '',
  new_password: '',
  confirm_password: '',
})

const validateConfirmPassword = (_rule: any, value: string, callback: any) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const profileRules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
  full_name: [
    { max: 100, message: '姓名最多100个字符', trigger: 'blur' },
  ],
}

const passwordRules: FormRules = {
  current_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' },
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度为6-100个字符', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

const formatDate = (date?: string | null) => {
  if (!date) return ''
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

const handleUpdateProfile = async () => {
  if (!profileFormRef.value) return
  
  await profileFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    profileLoading.value = true
    try {
      await userStore.updateProfile({
        email: profileForm.email,
        full_name: profileForm.full_name || undefined,
      })
    } catch (error) {
      console.error('Update profile error:', error)
    } finally {
      profileLoading.value = false
    }
  })
}

const handleUpdatePassword = async () => {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    passwordLoading.value = true
    try {
      await userStore.updatePassword(
        passwordForm.current_password,
        passwordForm.new_password
      )
      
      // Clear form
      passwordForm.current_password = ''
      passwordForm.new_password = ''
      passwordForm.confirm_password = ''
      passwordFormRef.value?.resetFields()
    } catch (error) {
      console.error('Update password error:', error)
    } finally {
      passwordLoading.value = false
    }
  })
}

onMounted(() => {
  // Refresh user info
  userStore.fetchUserInfo()
})
</script>

<style lang="scss" scoped>
.profile-page {
  max-width: 1200px;
  margin: 0 auto;
}

.profile-card {
  text-align: center;
  
  .user-header {
    .user-avatar {
      background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
      margin-bottom: 16px;
    }
    
    h2 {
      font-size: 24px;
      font-weight: 600;
      margin-bottom: 8px;
      color: var(--text-primary);
    }
    
    .user-email {
      color: var(--text-secondary);
      font-size: 14px;
      margin-bottom: 16px;
    }
    
    .user-roles {
      display: flex;
      justify-content: center;
      gap: 8px;
      flex-wrap: wrap;
    }
  }
  
  .user-info-list {
    text-align: left;
    
    .info-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 0;
      border-bottom: 1px solid var(--card-border);
      
      &:last-child {
        border-bottom: none;
      }
      
      .label {
        color: var(--text-secondary);
        font-size: 14px;
      }
      
      .value {
        color: var(--text-primary);
        font-size: 14px;
      }
    }
  }
}

.edit-card {
  .card-header {
    font-size: 16px;
    font-weight: 600;
  }
}
</style>
