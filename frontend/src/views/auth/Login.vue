<template>
  <div class="login-container">
    <div class="login-background">
      <div class="floating-shapes">
        <div v-for="n in 6" :key="n" class="shape" :class="`shape-${n}`"></div>
      </div>
    </div>
    
    <div class="login-card">
      <div class="login-header">
        <div class="logo">
          <el-icon :size="48"><Connection /></el-icon>
        </div>
        <h1>DDPS</h1>
        <p>药物-疾病关联预测系统</p>
      </div>
      
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            size="large"
            :prefix-icon="User"
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
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-btn"
            native-type="submit"
          >
            登 录
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <span>还没有账号？</span>
        <el-link type="primary" @click="goToRegister">立即注册</el-link>
      </div>
      
      <div class="demo-hint">
        <el-divider>演示账号</el-divider>
        <p>用户名: <code>admin</code> &nbsp; 密码: <code>admin123</code></p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { Connection, User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/store'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, message: '用户名至少3个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' },
  ],
}

const handleLogin = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      await userStore.login(form.username, form.password)
      
      ElMessage.success('登录成功')
      
      // Redirect to original page or dashboard
      const redirect = route.query.redirect as string
      router.push(redirect || '/dashboard')
    } catch (error: any) {
      console.error('Login error:', error)
      // Error message is handled by API interceptor
    } finally {
      loading.value = false
    }
  })
}

const goToRegister = () => {
  router.push('/register')
}
</script>

<style lang="scss" scoped>
.login-container {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.login-background {
  position: absolute;
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

.login-card {
  position: relative;
  width: 420px;
  padding: 48px 40px;
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid var(--card-border);
  border-radius: 24px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  animation: fadeIn 0.6s ease-out;
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
  
  .logo {
    width: 80px;
    height: 80px;
    margin: 0 auto 16px;
    background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
    border-radius: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    box-shadow: 0 10px 30px rgba(13, 115, 119, 0.4);
  }
  
  h1 {
    font-size: 32px;
    font-weight: 700;
    background: linear-gradient(135deg, var(--primary-light), #fff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 4px;
    margin-bottom: 8px;
  }
  
  p {
    color: var(--text-secondary);
    font-size: 14px;
  }
}

.login-form {
  .el-form-item {
    margin-bottom: 24px;
  }
  
  .login-btn {
    width: 100%;
    height: 48px;
    font-size: 16px;
    font-weight: 500;
    border-radius: 12px;
  }
}

.login-footer {
  text-align: center;
  margin-top: 24px;
  color: var(--text-secondary);
  
  .el-link {
    margin-left: 8px;
  }
}

.demo-hint {
  margin-top: 24px;
  text-align: center;
  
  :deep(.el-divider__text) {
    background: transparent;
    color: var(--text-muted);
    font-size: 12px;
  }
  
  p {
    color: var(--text-secondary);
    font-size: 13px;
    
    code {
      background: rgba(13, 115, 119, 0.2);
      color: var(--primary-light);
      padding: 2px 6px;
      border-radius: 4px;
      font-family: monospace;
    }
  }
}
</style>
