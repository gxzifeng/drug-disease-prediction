<template>
  <div class="dashboard fade-in">
    <div class="page-header">
      <h1>工作台</h1>
      <p>欢迎使用药物-疾病关联预测系统</p>
    </div>

    <!-- Stats Cards -->
    <el-row :gutter="24" class="stats-row">
      <el-col :span="6" v-for="stat in stats" :key="stat.title">
        <div class="stat-card glass-effect">
          <div class="stat-icon" :style="{ background: stat.gradient }">
            <el-icon :size="24"><component :is="stat.icon" /></el-icon>
          </div>
          <div class="stat-content">
            <span class="stat-value">{{ stat.value }}</span>
            <span class="stat-title">{{ stat.title }}</span>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- Quick Actions & Recent Activity -->
    <el-row :gutter="24" class="content-row">
      <el-col :span="16">
        <el-card class="quick-actions-card">
          <template #header>
            <div class="card-header">
              <span>快速操作</span>
            </div>
          </template>
          
          <div class="action-grid">
            <div 
              v-for="action in quickActions" 
              :key="action.title"
              class="action-item"
              @click="router.push(action.path)"
            >
              <div class="action-icon" :style="{ background: action.gradient }">
                <el-icon :size="28"><component :is="action.icon" /></el-icon>
              </div>
              <div class="action-info">
                <span class="action-title">{{ action.title }}</span>
                <span class="action-desc">{{ action.description }}</span>
              </div>
              <el-icon class="action-arrow"><ArrowRight /></el-icon>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="system-status-card">
          <template #header>
            <div class="card-header">
              <span>系统状态</span>
              <el-button text size="small" @click="refreshStatus">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>
          
          <div class="status-list">
            <div class="status-item" v-for="service in serviceStatus" :key="service.name">
              <div class="status-info">
                <span class="status-name">{{ service.name }}</span>
                <el-tag 
                  :type="service.status === 'connected' ? 'success' : 'danger'"
                  size="small"
                >
                  {{ service.status === 'connected' ? '正常' : '异常' }}
                </el-tag>
              </div>
              <div class="status-bar">
                <div 
                  class="status-progress" 
                  :style="{ 
                    width: service.status === 'connected' ? '100%' : '30%',
                    background: service.status === 'connected' ? 'var(--success-color)' : 'var(--error-color)'
                  }"
                ></div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Pipeline Overview -->
    <el-card class="pipeline-card">
      <template #header>
        <div class="card-header">
          <span>预测流程概览</span>
        </div>
      </template>
      
      <div class="pipeline">
        <div v-for="(step, index) in pipelineSteps" :key="step.title" class="pipeline-step">
          <div class="step-connector" v-if="index > 0">
            <el-icon><ArrowRight /></el-icon>
          </div>
          <div class="step-card" :class="{ active: step.active }">
            <div class="step-icon">
              <el-icon :size="24"><component :is="step.icon" /></el-icon>
            </div>
            <span class="step-title">{{ step.title }}</span>
            <span class="step-desc">{{ step.description }}</span>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Document, Share, Cpu, Connection, Box, DataAnalysis,
  ArrowRight, Refresh, Upload, TrendCharts
} from '@element-plus/icons-vue'
import { healthApi } from '@/api/health'

const router = useRouter()

const stats = ref([
  { title: '数据集', value: '0', icon: Document, gradient: 'linear-gradient(135deg, #667eea, #764ba2)' },
  { title: '训练模型', value: '0', icon: Box, gradient: 'linear-gradient(135deg, #f093fb, #f5576c)' },
  { title: '预测任务', value: '0', icon: TrendCharts, gradient: 'linear-gradient(135deg, #4facfe, #00f2fe)' },
  { title: '关联发现', value: '0', icon: Connection, gradient: 'linear-gradient(135deg, #43e97b, #38f9d7)' },
])

const quickActions = [
  { 
    title: '上传数据集', 
    description: '上传药物-疾病关联数据', 
    icon: Upload,
    path: '/datasets',
    gradient: 'linear-gradient(135deg, #667eea, #764ba2)'
  },
  { 
    title: '构建网络', 
    description: '从数据构建关联网络', 
    icon: Share,
    path: '/graphs',
    gradient: 'linear-gradient(135deg, #f093fb, #f5576c)'
  },
  { 
    title: '训练模型', 
    description: '训练表示学习与分类模型', 
    icon: Cpu,
    path: '/training',
    gradient: 'linear-gradient(135deg, #4facfe, #00f2fe)'
  },
  { 
    title: '开始预测', 
    description: '预测药物-疾病关联', 
    icon: Connection,
    path: '/prediction',
    gradient: 'linear-gradient(135deg, #43e97b, #38f9d7)'
  },
]

const serviceStatus = ref([
  { name: 'API 服务', status: 'checking' },
  { name: '数据库', status: 'checking' },
  { name: 'Redis 缓存', status: 'checking' },
])

const pipelineSteps = [
  { title: '数据上传', description: 'CSV/TSV', icon: Upload, active: false },
  { title: '网络构建', description: '二部图/异构图', icon: Share, active: false },
  { title: '表示学习', description: 'Node2Vec/GCN', icon: Cpu, active: false },
  { title: '分类训练', description: 'RF/XGBoost', icon: Box, active: false },
  { title: '关联预测', description: '单例/批量', icon: Connection, active: false },
  { title: '结果分析', description: '可视化/解释', icon: DataAnalysis, active: false },
]

const refreshStatus = async () => {
  try {
    const response = await healthApi.checkFull()
    serviceStatus.value = [
      { name: 'API 服务', status: response.data?.status === 'healthy' ? 'connected' : 'error' },
      { name: '数据库', status: response.data?.database === 'connected' ? 'connected' : 'error' },
      { name: 'Redis 缓存', status: response.data?.redis === 'connected' ? 'connected' : 'error' },
    ]
  } catch {
    serviceStatus.value = serviceStatus.value.map(s => ({ ...s, status: 'error' }))
  }
}

onMounted(() => {
  refreshStatus()
})
</script>

<style lang="scss" scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 32px;
  
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

.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: transform var(--transition-normal), box-shadow var(--transition-normal);
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.2);
  }
  
  .stat-icon {
    width: 56px;
    height: 56px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    flex-shrink: 0;
  }
  
  .stat-content {
    display: flex;
    flex-direction: column;
    
    .stat-value {
      font-size: 28px;
      font-weight: 700;
      color: var(--text-primary);
      font-family: 'JetBrains Mono', monospace;
    }
    
    .stat-title {
      font-size: 14px;
      color: var(--text-secondary);
    }
  }
}

.content-row {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  color: var(--text-primary);
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  cursor: pointer;
  transition: all var(--transition-normal);
  
  &:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: var(--primary-light);
    transform: translateX(4px);
    
    .action-arrow {
      opacity: 1;
      transform: translateX(0);
    }
  }
  
  .action-icon {
    width: 52px;
    height: 52px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    flex-shrink: 0;
  }
  
  .action-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    
    .action-title {
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 4px;
    }
    
    .action-desc {
      font-size: 12px;
      color: var(--text-secondary);
    }
  }
  
  .action-arrow {
    color: var(--primary-light);
    opacity: 0;
    transform: translateX(-8px);
    transition: all var(--transition-normal);
  }
}

.status-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.status-item {
  .status-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    
    .status-name {
      color: var(--text-primary);
      font-weight: 500;
    }
  }
  
  .status-bar {
    height: 4px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
    overflow: hidden;
    
    .status-progress {
      height: 100%;
      border-radius: 2px;
      transition: width 0.5s ease;
    }
  }
}

.pipeline-card {
  margin-top: 24px;
}

.pipeline {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 20px 0;
}

.pipeline-step {
  display: flex;
  align-items: center;
  flex: 1;
  
  .step-connector {
    color: var(--text-muted);
    margin: 0 8px;
  }
  
  .step-card {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 20px 12px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    transition: all var(--transition-normal);
    
    &:hover {
      border-color: var(--primary-light);
      background: rgba(255, 255, 255, 0.04);
    }
    
    &.active {
      border-color: var(--primary-light);
      background: rgba(13, 115, 119, 0.1);
      
      .step-icon {
        background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
        color: white;
      }
    }
    
    .step-icon {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      background: rgba(255, 255, 255, 0.05);
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--text-secondary);
      margin-bottom: 12px;
    }
    
    .step-title {
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 4px;
    }
    
    .step-desc {
      font-size: 12px;
      color: var(--text-secondary);
    }
  }
}
</style>
