<template>
  <div class="model-list fade-in">
    <div class="page-header">
      <h1>模型管理</h1>
      <p>管理训练好的预测模型，选择激活模型用于预测服务</p>
    </div>

    <!-- Summary Cards -->
    <el-row :gutter="20" class="summary-cards">
      <el-col :span="6">
        <el-card class="summary-card">
          <div class="summary-content">
            <div class="summary-icon" style="background: var(--el-color-primary-light-9)">
              <el-icon size="24" color="var(--el-color-primary)"><Box /></el-icon>
            </div>
            <div class="summary-info">
              <div class="summary-value">{{ totalModels }}</div>
              <div class="summary-label">总模型数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="summary-card">
          <div class="summary-content">
            <div class="summary-icon" style="background: var(--el-color-success-light-9)">
              <el-icon size="24" color="var(--el-color-success)"><CircleCheck /></el-icon>
            </div>
            <div class="summary-info">
              <div class="summary-value">{{ completedModels }}</div>
              <div class="summary-label">已完成</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="summary-card">
          <div class="summary-content">
            <div class="summary-icon" style="background: var(--el-color-warning-light-9)">
              <el-icon size="24" color="var(--el-color-warning)"><Star /></el-icon>
            </div>
            <div class="summary-info">
              <div class="summary-value">{{ activeModel?.name || '未设置' }}</div>
              <div class="summary-label">激活模型</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="summary-card">
          <div class="summary-content">
            <div class="summary-icon" style="background: var(--el-color-info-light-9)">
              <el-icon size="24" color="var(--el-color-info)"><TrendCharts /></el-icon>
            </div>
            <div class="summary-info">
              <div class="summary-value">{{ bestAUC }}</div>
              <div class="summary-label">最佳 AUC-ROC</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Model List -->
    <el-card class="model-table-card">
      <template #header>
        <div class="card-header">
          <div class="left">
            <span>已完成的模型</span>
            <el-button 
              v-if="selectedIds.length >= 2" 
              type="warning" 
              size="small" 
              class="compare-btn"
              @click="handleCompare"
            >
              对比所选 ({{ selectedIds.length }})
            </el-button>
          </div>
          <el-button type="primary" link @click="goToExperiments">
            前往分类器实验 →
          </el-button>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="completedExperiments"
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="模型名称" min-width="150">
          <template #default="{ row }">
            <div class="name-cell">
              <span>{{ row.name }}</span>
              <el-tag v-if="row.is_active" type="success" size="small" effect="dark">激活</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="classifier" label="分类器" width="130">
          <template #default="{ row }">
            <el-tag :type="getClassifierType(row.classifier)" size="small">
              {{ getClassifierName(row.classifier) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="AUC-ROC" width="120">
          <template #default="{ row }">
            <span :class="{ 'best-metric': isBestAUC(row) }">
              {{ formatMetric(row.auc_roc) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="F1 Score" width="120">
          <template #default="{ row }">
            <span :class="{ 'best-metric': isBestF1(row) }">
              {{ formatMetric(row.f1_score) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="Accuracy" width="120">
          <template #default="{ row }">
            {{ formatMetric(row.accuracy) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="训练时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="!row.is_active"
              type="primary"
              link
              size="small"
              @click="handleActivate(row)"
            >
              激活
            </el-button>
            <el-button
              type="info"
              link
              size="small"
              @click="viewDetail(row)"
            >
              详情
            </el-button>
            <el-button
              type="danger"
              link
              size="small"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
        </el-table>  
    </el-card>

    <!-- Detail Dialog -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="selectedExperiment?.name || '模型详情'"
      width="800px"
    >
      <template v-if="selectedExperiment">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="模型 ID">{{ selectedExperiment.id }}</el-descriptions-item>
          <el-descriptions-item label="名称">{{ selectedExperiment.name }}</el-descriptions-item>
          <el-descriptions-item label="分类器">
            <el-tag :type="getClassifierType(selectedExperiment.classifier)">
              {{ getClassifierName(selectedExperiment.classifier) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="特征方法">
            {{ getFeatureMethodName(selectedExperiment.feature_method) }}
          </el-descriptions-item>
          <el-descriptions-item label="AUC-ROC">
            {{ formatMetric(selectedExperiment.auc_roc) }}
          </el-descriptions-item>
          <el-descriptions-item label="AUC-PR">
            {{ formatMetric(selectedExperiment.auc_pr) }}
          </el-descriptions-item>
          <el-descriptions-item label="F1 Score">
            {{ formatMetric(selectedExperiment.f1_score) }}
          </el-descriptions-item>
          <el-descriptions-item label="Accuracy">
            {{ formatMetric(selectedExperiment.accuracy) }}
          </el-descriptions-item>
          <el-descriptions-item label="Precision">
            {{ formatMetric(selectedExperiment.precision) }}
          </el-descriptions-item>
          <el-descriptions-item label="Recall">
            {{ formatMetric(selectedExperiment.recall) }}
          </el-descriptions-item>
          <el-descriptions-item label="训练样本">
            {{ selectedExperiment.num_train_samples || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="测试样本">
            {{ selectedExperiment.num_test_samples || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="训练时间">
            {{ selectedExperiment.training_time_seconds ? `${selectedExperiment.training_time_seconds.toFixed(2)}s` : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDate(selectedExperiment.created_at) }}
          </el-descriptions-item>
        </el-descriptions>
        
        <div v-if="selectedExperiment.classifier_params" class="params-section">
          <h4>分类器参数</h4>
          <el-descriptions :column="3" border size="small">
            <el-descriptions-item 
              v-for="(value, key) in selectedExperiment.classifier_params" 
              :key="key" 
              :label="String(key)"
            >
              {{ value ?? '空' }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </template>
      
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button 
          v-if="selectedExperiment && !selectedExperiment.is_active"
          type="primary"
          @click="handleActivate(selectedExperiment)"
        >
          设为激活模型
        </el-button>
      </template>
    </el-dialog>

    <!-- Comparison Dialog -->
    <el-dialog
      v-model="compareDialogVisible"
      title="模型对比"
      width="90%"
      class="compare-dialog"
    >
      <div v-if="comparisonData" class="comparison-container">
        <el-table :data="comparisonMetrics" border stripe>
          <el-table-column prop="metric" label="指标" width="150" fixed />
          <el-table-column 
            v-for="exp in comparisonData.experiments" 
            :key="exp.id" 
            :label="exp.name"
            min-width="150"
          >
            <template #default="{ row }">
              <div :class="{ 'highlight-best': isBestInComparison(exp.id, row.key) }">
                {{ row.values[exp.id] }}
                <el-icon v-if="isBestInComparison(exp.id, row.key)" color="var(--el-color-warning)"><StarFilled /></el-icon>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <div class="comparison-charts">
          <!-- 这里可以添加对比图表 -->
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Box, CircleCheck, Star, StarFilled, TrendCharts } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

import {
  listModels,
  getActiveModel,
  activateModel,
  deleteModel,
  compareModels,
} from '@/api/models'
import { Experiment, ExperimentComparison } from '@/api/experiments'

const router = useRouter()

// State
const loading = ref(false)
const experiments = ref<Experiment[]>([])
const activeModel = ref<Experiment | null>(null)
const selectedExperiment = ref<Experiment | null>(null)
const detailDialogVisible = ref(false)
const compareDialogVisible = ref(false)
const selectedIds = ref<number[]>([])
const comparisonData = ref<ExperimentComparison | null>(null)

// Computed
const totalModels = computed(() => experiments.value.length)
const completedModels = computed(() => experiments.value.filter(e => e.status === 'completed').length)
const completedExperiments = computed(() => experiments.value.filter(e => e.status === 'completed'))

const bestAUC = computed(() => {
  const completed = completedExperiments.value
  if (completed.length === 0) return '-'
  const best = Math.max(...completed.map(e => e.auc_roc || 0))
  return formatMetric(best)
})

const bestAUCValue = computed(() => {
  const completed = completedExperiments.value
  if (completed.length === 0) return 0
  return Math.max(...completed.map(e => e.auc_roc || 0))
})

const bestF1Value = computed(() => {
  const completed = completedExperiments.value
  if (completed.length === 0) return 0
  return Math.max(...completed.map(e => e.f1_score || 0))
})

const comparisonMetrics = computed(() => {
  if (!comparisonData.value) return []
  const exps = comparisonData.value.experiments
  
  const metrics = [
    { name: '分类器', key: 'classifier' },
    { name: 'AUC-ROC', key: 'auc_roc' },
    { name: 'F1 Score', key: 'f1_score' },
    { name: 'Accuracy', key: 'accuracy' },
    { name: 'Precision', key: 'precision' },
    { name: 'Recall', key: 'recall' },
    { name: 'AUC-PR', key: 'auc_pr' },
    { name: '特征方法', key: 'feature_method' },
    { name: '训练时间', key: 'training_time' },
  ]

  return metrics.map(m => {
    const rowValues: Record<number, any> = {}
    exps.forEach(exp => {
      let val = (exp as any)[m.key]
      if (['auc_roc', 'f1_score', 'accuracy', 'precision', 'recall', 'auc_pr'].includes(m.key)) {
        val = formatMetric(val)
      } else if (m.key === 'classifier') {
        val = getClassifierName(val)
      } else if (m.key === 'feature_method') {
        val = getFeatureMethodName(val)
      } else if (m.key === 'training_time') {
        val = exp.training_time_seconds ? `${exp.training_time_seconds.toFixed(2)}s` : '-'
      }
      rowValues[exp.id] = val
    })
    return {
      metric: m.name,
      key: m.key,
      values: rowValues
    }
  })
})

// Methods
const formatDate = (dateStr: string) => {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

const formatMetric = (value: number | null | undefined) => {
  if (value === null || value === undefined) return '-'
  return (value * 100).toFixed(2) + '%'
}

const getClassifierType = (classifier: string) => {
  const types: Record<string, string> = {
    random_forest: 'primary',
    xgboost: 'success',
    svm: 'warning',
  }
  return types[classifier] || 'info'
}

const getClassifierName = (classifier: string) => {
  const names: Record<string, string> = {
    random_forest: 'Random Forest',
    xgboost: 'XGBoost',
    svm: 'SVM',
  }
  return names[classifier] || classifier
}

const getFeatureMethodName = (method: string) => {
  const names: Record<string, string> = {
    concat: 'Concat',
    hadamard: 'Hadamard',
    l1: 'L1',
    l2: 'L2',
    average: 'Average',
  }
  return names[method] || method
}

const isBestAUC = (exp: Experiment) => {
  return exp.auc_roc === bestAUCValue.value && bestAUCValue.value > 0
}

const isBestF1 = (exp: Experiment) => {
  return exp.f1_score === bestF1Value.value && bestF1Value.value > 0
}

const fetchExperiments = async () => {
  loading.value = true
  try {
    const response = await listModels(1, 100)
    experiments.value = response.data.items
  } catch (error) {
    console.error('Failed to fetch models:', error)
  } finally {
    loading.value = false
  }
}

const fetchActiveModel = async () => {
  try {
    const response = await getActiveModel()
    activeModel.value = response.data
  } catch (error) {
    console.error('Failed to fetch active model:', error)
  }
}

const viewDetail = (experiment: Experiment) => {
  selectedExperiment.value = experiment
  detailDialogVisible.value = true
}

const handleActivate = async (experiment: Experiment) => {
  try {
    await ElMessageBox.confirm(
      `确定要将 "${experiment.name}" 设为激活模型吗？这将用于预测服务。`,
      '激活模型',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info',
      }
    )

    await activateModel(experiment.id)
    ElMessage.success('模型已激活')
    detailDialogVisible.value = false
    fetchExperiments()
    fetchActiveModel()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to activate model:', error)
    }
  }
}

const handleDelete = async (experiment: Experiment) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模型 "${experiment.name}" 吗？此操作不可撤销，且将删除相关的模型文件。`,
      '删除模型',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        confirmButtonClass: 'el-button--danger',
        type: 'warning',
      }
    )

    await deleteModel(experiment.id)
    ElMessage.success('模型已删除')
    fetchExperiments()
    if (activeModel.value?.id === experiment.id) {
      fetchActiveModel()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete model:', error)
    }
  }
}

const handleSelectionChange = (selection: Experiment[]) => {
  selectedIds.value = selection.map(s => s.id)
}

const handleCompare = async () => {
  if (selectedIds.value.length < 2) return
  
  try {
    const response = await compareModels(selectedIds.value)
    comparisonData.value = response.data
    compareDialogVisible.value = true
  } catch (error) {
    console.error('Failed to compare models:', error)
    ElMessage.error('对比失败')
  }
}

const isBestInComparison = (expId: number, metricKey: string) => {
  if (!comparisonData.value) return false
  if (metricKey === 'auc_roc') return comparisonData.value.best_by_auc_roc === expId
  if (metricKey === 'f1_score') return comparisonData.value.best_by_f1 === expId
  return false
}

const goToExperiments = () => {
  router.push('/experiments')
}

// Lifecycle
onMounted(() => {
  fetchExperiments()
  fetchActiveModel()
})
</script>

<style lang="scss" scoped>
.model-list {
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

.summary-cards {
  margin-bottom: 24px;
  
  .summary-card {
    .summary-content {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    
    .summary-icon {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .summary-info {
      .summary-value {
        font-size: 24px;
        font-weight: 600;
        color: var(--text-primary);
        line-height: 1.2;
        max-width: 150px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      
      .summary-label {
        font-size: 13px;
        color: var(--text-secondary);
        margin-top: 4px;
      }
    }
  }
}

.model-table-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .left {
      display: flex;
      align-items: center;
      gap: 16px;
    }
  }
}

.name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.best-metric {
  color: var(--el-color-success);
  font-weight: 600;
  
  &::after {
    content: ' ⭐';
  }
}

.params-section {
  margin-top: 20px;

  h4 {
    margin-bottom: 12px;
    color: var(--text-primary);
    font-weight: 500;
  }
}

.highlight-best {
  color: var(--el-color-warning);
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 4px;
}

.compare-dialog {
  :deep(.el-dialog__body) {
    padding-top: 10px;
  }
}

.comparison-container {
  overflow-x: auto;
}
</style>
