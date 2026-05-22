<template>
  <div class="settings fade-in">
    <div class="page-header">
      <h1>系统设置</h1>
      <p>配置系统参数与用户偏好（仅管理员可访问，设置保存在本机浏览器）</p>
    </div>

    <el-row :gutter="24">
      <el-col :span="16">
        <el-card>
          <template #header>
            <span>基本设置</span>
            <el-button type="primary" size="small" @click="handleSave">保存设置</el-button>
          </template>
          
          <el-form label-width="120px">
            <el-form-item label="系统语言">
              <el-select v-model="settings.language" style="width: 200px">
                <el-option label="简体中文" value="zh-CN" />
                <el-option label="English" value="en-US" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="主题模式">
              <el-radio-group v-model="settings.theme">
                <el-radio-button label="dark">深色</el-radio-button>
                <el-radio-button label="light">浅色</el-radio-button>
                <el-radio-button label="auto">跟随系统</el-radio-button>
              </el-radio-group>
              <span class="form-tip">主题切换后刷新页面生效</span>
            </el-form-item>
            
            <el-form-item label="侧边栏">
              <el-switch v-model="settings.sidebarCollapsed" />
              <span class="form-tip">下次进入时默认折叠侧边栏</span>
            </el-form-item>
          </el-form>
        </el-card>
        
        <el-card style="margin-top: 24px">
          <template #header>
            <span>训练默认参数</span>
          </template>
          <p class="form-desc">创建新训练/实验时，表单将优先使用以下默认值（若接口支持）。</p>
          <el-form label-width="120px">
            <el-form-item label="随机种子">
              <el-input-number v-model="settings.randomSeed" :min="0" :max="99999" />
              <span class="form-tip">用于实验可复现</span>
            </el-form-item>
            
            <el-form-item label="嵌入维度">
              <el-input-number v-model="settings.embeddingDim" :min="32" :max="512" :step="32" />
            </el-form-item>
            
            <el-form-item label="默认学习率">
              <el-input-number v-model="settings.learningRate" :min="0.0001" :max="0.1" :step="0.001" :precision="4" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>系统信息</span>
          </template>
          
          <div class="info-list">
            <div class="info-item">
              <span class="info-label">版本号</span>
              <span class="info-value">v1.0.0</span>
            </div>
            <div class="info-item">
              <span class="info-label">前端框架</span>
              <span class="info-value">Vue 3 + Element Plus</span>
            </div>
            <div class="info-item">
              <span class="info-label">后端框架</span>
              <span class="info-value">FastAPI</span>
            </div>
            <div class="info-item">
              <span class="info-label">数据库</span>
              <span class="info-value">MySQL</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getAppSettings, setAppSettings, type AppSettings } from '@/utils/settings'

const settings = reactive<AppSettings>({
  language: 'zh-CN',
  theme: 'dark',
  sidebarCollapsed: false,
  randomSeed: 42,
  embeddingDim: 128,
  learningRate: 0.001,
})

onMounted(() => {
  const saved = getAppSettings()
  settings.language = saved.language
  settings.theme = saved.theme
  settings.sidebarCollapsed = saved.sidebarCollapsed
  settings.randomSeed = saved.randomSeed
  settings.embeddingDim = saved.embeddingDim
  settings.learningRate = saved.learningRate
})

const handleSave = () => {
  setAppSettings(settings)
  ElMessage.success('设置已保存，部分选项刷新页面后生效')
}
</script>

<style lang="scss" scoped>
.settings {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
  
  h1 {
    font-size: 28px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 8px;
  }
  
  p {
    color: var(--text-secondary);
  }
}

.form-tip {
  margin-left: 12px;
  font-size: 12px;
  color: var(--text-muted);
}

.form-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 16px;
}

.el-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--card-border);
  
  &:last-child {
    border-bottom: none;
    padding-bottom: 0;
  }
  
  .info-label {
    color: var(--text-secondary);
  }
  
  .info-value {
    color: var(--text-primary);
    font-weight: 500;
  }
}
</style>
