<template>
  <div class="register-container">
    <div class="register-background">
      <div class="floating-shapes">
        <div v-for="n in 6" :key="n" class="shape" :class="`shape-${n}`"></div>
      </div>
    </div>
    
    <div class="register-card">
      <div class="register-header">
        <div class="logo">
          <el-icon :size="48"><Connection /></el-icon>
        </div>
        <h1>注册账号</h1>
        <p>创建您的DDPS账号</p>
      </div>
      
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="register-form"
        @submit.prevent="handleRegister"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>
        
        <el-form-item prop="email">
          <el-input
            v-model="form.email"
            placeholder="邮箱"
            size="large"
            :prefix-icon="Message"
          />
        </el-form-item>
        
        <el-form-item prop="full_name">
          <el-input
            v-model="form.full_name"
            placeholder="姓名（可选）"
            size="large"
            :prefix-icon="Postcard"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            size="large"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        
        <el-form-item prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="确认密码"
            size="large"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleRegister"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="register-btn"
            native-type="submit"
          >
            注 册
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="register-footer">
        <span>已有账号？</span>
        <el-link type="primary" @click="goToLogin">立即登录</el-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { Connection, User, Lock, Message, Postcard } from '@element-plus/icons-vue'
import { useUserStore } from '@/store'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  username: '',
  email: '',
  full_name: '',
  password: '',
  confirmPassword: '',
})

const validateConfirmPassword = (_rule: any, value: string, callback: any) => {
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为3-50个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
  full_name: [
    { max: 100, message: '姓名最多100个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度为6-100个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

const handleRegister = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      await userStore.register({
        username: form.username,
        email: form.email,
        password: form.password,
        full_name: form.full_name || undefined,
      })
      
      ElMessage.success('注册成功，请登录')
      router.push('/login')
    } catch (error: any) {
      console.error('Register error:', error)
      // Error message is handled by API interceptor
    } finally {
      loading.value = false
    }
  })
}

const goToLogin = () => {
  router.push('/login')
}
</script>

<style lang="scss" scoped>
.register-container {
  width: 100%;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  padding: 40px 20px;
}

.register-background {
  position: fixed;
  inset: 0;
  background: var(--bg-gradient);
  
  .floating-shapes {
    position: absolute;
    inset: 0;
    overflow: hidden;
  }
  
  .shape {
    position: absolute;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
    opacity: 0.1;
    animation: float 20s infinite ease-in-out;
    
    &.shape-1 {
      width: 400px;
      height: 400px;
      top: -100px;
      left: -100px;
      animation-delay: 0s;
    }
    
    &.shape-2 {
      width: 300px;
      height: 300px;
      top: 50%;
      right: -100px;
      animation-delay: -5s;
    }
    
    &.shape-3 {
      width: 200px;
      height: 200px;
      bottom: -50px;
      left: 30%;
      animation-delay: -10s;
    }
    
    &.shape-4 {
      width: 150px;
      height: 150px;
      top: 20%;
      left: 60%;
      background: linear-gradient(135deg, var(--accent-color), var(--accent-light));
      animation-delay: -3s;
    }
    
    &.shape-5 {
      width: 100px;
      height: 100px;
      bottom: 30%;
      left: 10%;
      animation-delay: -7s;
    }
    
    &.shape-6 {
      width: 250px;
      height: 250px;
      top: 60%;
      right: 20%;
      animation-delay: -12s;
    }
  }
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) rotate(0deg);
  }
  25% {
    transform: translate(20px, -30px) rotate(5deg);
  }
  50% {
    transform: translate(-20px, 20px) rotate(-5deg);
  }
  75% {
    transform: translate(30px, 10px) rotate(3deg);
  }
}

.register-card {
  position: relative;
  width: 420px;
  padding: 40px;
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid var(--card-border);
  border-radius: 24px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  animation: fadeIn 0.6s ease-out;
}

.register-header {
  text-align: center;
  margin-bottom: 32px;
  
  .logo {
    width: 72px;
    height: 72px;
    margin: 0 auto 16px;
    background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
    border-radius: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    box-shadow: 0 10px 30px rgba(13, 115, 119, 0.4);
  }
  
  h1 {
    font-size: 28px;
    font-weight: 700;
    background: linear-gradient(135deg, var(--primary-light), #fff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 2px;
    margin-bottom: 8px;
  }
  
  p {
    color: var(--text-secondary);
    font-size: 14px;
  }
}

.register-form {
  .el-form-item {
    margin-bottom: 20px;
  }
  
  .register-btn {
    width: 100%;
    height: 48px;
    font-size: 16px;
    font-weight: 500;
    border-radius: 12px;
  }
}

.register-footer {
  text-align: center;
  margin-top: 20px;
  color: var(--text-secondary);
  
  .el-link {
    margin-left: 8px;
  }
}
</style>
