<template>
  <div class="prediction fade-in">
    <div class="page-header">
      <h1>关联预测</h1>
      <p>预测药物-疾病潜在关联</p>
    </div>

    <el-tabs v-model="activeTab" class="prediction-tabs">
      <!-- Single Prediction Tab -->
      <el-tab-pane label="单例预测" name="single">
        <el-card shadow="never" class="tab-card">
          <template #header>
            <div class="card-header">
              <span>输入药物和疾病 ID 进行单例预测</span>
              <el-tag v-if="activeModel" type="success" size="small">
                当前模型: {{ activeModel.name }}
              </el-tag>
            </div>
          </template>

          <el-form
            ref="singleFormRef"
            :model="singleForm"
            :rules="singleRules"
            label-width="100px"
            class="prediction-form"
          >
            <el-form-item label="药物 ID" prop="drug_id">
              <el-input v-model="singleForm.drug_id" placeholder="例如: DB00001" />
            </el-form-item>
            <el-form-item label="疾病 ID" prop="disease_id">
              <el-input v-model="singleForm.disease_id" placeholder="例如: D000001" />
            </el-form-item>
            <el-form-item label="选择模型" prop="model_id">
              <el-select v-model="singleForm.model_id" placeholder="留空则使用当前活跃模型" clearable filterable>
                <el-option
                  v-for="model in completedModels"
                  :key="model.id"
                  :label="model.name"
                  :value="model.id"
                >
                  <span style="float: left">{{ model.name }}</span>
                  <span style="float: right; color: var(--el-text-color-secondary); font-size: 13px">
                    {{ model.classifier }}
                  </span>
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="singleLoading" @click="handleSinglePredict">
                开始预测
              </el-button>
              <el-button @click="resetSingleForm">重置</el-button>
            </el-form-item>
          </el-form>

          <!-- Single Prediction Result -->
          <div v-if="singleResult" class="prediction-result mt-4">
            <el-divider>预测结果</el-divider>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="药物 ID">{{ singleResult.drug_id }}</el-descriptions-item>
              <el-descriptions-item label="疾病 ID">{{ singleResult.disease_id }}</el-descriptions-item>
              <el-descriptions-item label="关联概率">
                <el-progress 
                  :percentage="Math.round(singleResult.probability * 100)" 
                  :color="getProgressColor(singleResult.probability)"
                />
              </el-descriptions-item>
              <el-descriptions-item label="预测结论">
                <el-tag :type="singleResult.label === 1 ? 'success' : 'info'">
                  {{ singleResult.label === 1 ? '存在关联' : '不存在关联' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="使用模型">{{ singleResult.model_name }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- Batch Prediction Tab -->
      <el-tab-pane label="批量预测" name="batch">
        <el-card shadow="never" class="tab-card">
          <template #header>
            <div class="card-header">
              <span>选择数据集进行批量关联预测</span>
            </div>
          </template>

          <el-form
            ref="batchFormRef"
            :model="batchForm"
            :rules="batchRules"
            label-width="100px"
            class="prediction-form"
          >
            <el-form-item label="选择数据集" prop="dataset_id">
              <el-select v-model="batchForm.dataset_id" placeholder="选择包含待预测对的数据集" filterable>
                <el-option
                  v-for="ds in datasets"
                  :key="ds.id"
                  :label="ds.name"
                  :value="ds.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="选择模型" prop="model_id">
              <el-select v-model="batchForm.model_id" placeholder="留空则使用当前活跃模型" clearable filterable>
                <el-option
                  v-for="model in completedModels"
                  :key="model.id"
                  :label="model.name"
                  :value="model.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="batchLoading" @click="handleBatchPredict">
                开始批量预测
              </el-button>
            </el-form-item>
          </el-form>

          <!-- Batch Tasks List -->
          <div v-if="batchTasks.length > 0" class="batch-tasks mt-4">
            <el-divider>预测任务</el-divider>
            <el-table :data="batchTasks" style="width: 100%">
              <el-table-column prop="task_id" label="任务 ID" width="220" />
              <el-table-column label="状态" width="120">
                <template #default="{ row }">
                  <el-tag :type="getStatusTag(row.status)">{{ row.status }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="进度">
                <template #default="{ row }">
                  <el-progress :percentage="row.progress" />
                  <div class="task-message">{{ row.message }}</div>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150">
                <template #default="{ row }">
                  <el-button 
                    v-if="row.status === 'SUCCESS' && row.result && row.result.filename"
                    type="primary" 
                    link 
                    @click="downloadResults(row.result.filename)"
                  >
                    下载结果
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- Recommendation Tab -->
      <el-tab-pane label="推荐" name="recommend">
        <el-card shadow="never" class="tab-card">
          <template #header>
            <div class="card-header">
              <span>基于已训练模型的 Top-K 推荐</span>
              <el-segmented
                v-model="recommendMode"
                :options="[
                  { label: '疾病 → 药物', value: 'disease_to_drugs' },
                  { label: '药物 → 疾病', value: 'drug_to_diseases' }
                ]"
              />
            </div>
          </template>

          <el-form
            :model="recommendForm"
            label-width="100px"
            class="prediction-form"
          >
            <el-form-item v-if="recommendMode === 'disease_to_drugs'" label="疾病 ID">
              <el-input
                v-model="recommendForm.disease_id"
                placeholder="例如: D000001"
              />
            </el-form-item>
            <el-form-item v-else label="药物 ID">
              <el-input
                v-model="recommendForm.drug_id"
                placeholder="例如: DB00001"
              />
            </el-form-item>

            <el-form-item label="Top-K">
              <el-input-number
                v-model="recommendForm.top_k"
                :min="1"
                :max="200"
              />
            </el-form-item>

            <el-form-item label="选择模型">
              <el-select
                v-model="recommendForm.model_id"
                placeholder="留空则使用当前活跃模型"
                clearable
                filterable
              >
                <el-option
                  v-for="model in completedModels"
                  :key="model.id"
                  :label="model.name"
                  :value="model.id"
                />
              </el-select>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                :loading="recommendLoading"
                @click="handleRecommend"
              >
                获取推荐
              </el-button>
              <el-button @click="resetRecommend">重置</el-button>
            </el-form-item>
          </el-form>

          <!-- Recommendation Result -->
          <div v-if="recommendItems.length" class="mt-4">
            <el-divider>推荐结果（按概率降序）</el-divider>
            <el-table :data="recommendItems" style="width: 100%">
              <el-table-column
                label="#"
                type="index"
                width="60"
              />
              <el-table-column
                v-if="recommendMode === 'disease_to_drugs'"
                prop="drug_id"
                label="药物 ID"
                min-width="160"
              />
              <el-table-column
                v-else
                prop="disease_id"
                label="疾病 ID"
                min-width="160"
              />
              <el-table-column label="概率" min-width="200">
                <template #default="{ row }">
                  <el-progress
                    :percentage="Math.round(row.probability * 100)"
                    :color="getProgressColor(row.probability)"
                  />
                </template>
              </el-table-column>
              <el-table-column label="预测结论" width="120">
                <template #default="{ row }">
                  <el-tag
                    v-if="row.label === 1"
                    type="success"
                    size="small"
                  >
                    存在关联
                  </el-tag>
                  <el-tag
                    v-else-if="row.label === 0"
                    type="info"
                    size="small"
                  >
                    不存在关联
                  </el-tag>
                  <el-text v-else type="info" size="small">
                    未提供
                  </el-text>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <el-empty
            v-else
            class="mt-4"
            description="请输入条件并点击“获取推荐”"
          />
        </el-card>
      </el-tab-pane>

      <!-- History Tab -->
      <el-tab-pane label="历史记录" name="history">
        <el-card shadow="never" class="tab-card">
          <template #header>
            <div class="card-header">
              <span>预测历史</span>
              <div class="history-filters">
                <el-select
                  v-model="historyQuery.type"
                  placeholder="类型"
                  clearable
                  style="width: 140px"
                  @change="handleHistoryFilterChange"
                >
                  <el-option label="单例预测" value="single" />
                  <el-option label="批量预测" value="batch" />
                  <el-option label="推荐" value="recommendation" />
                </el-select>
                <el-select
                  v-model="historyQuery.experiment_id"
                  placeholder="模型"
                  clearable
                  filterable
                  style="width: 180px"
                  @change="handleHistoryFilterChange"
                >
                  <el-option
                    v-for="model in completedModels"
                    :key="model.id"
                    :label="model.name"
                    :value="model.id"
                  />
                </el-select>
                <el-button
                  type="primary"
                  link
                  :loading="historyLoading"
                  @click="fetchHistory"
                >
                  刷新
                </el-button>
              </div>
            </div>
          </template>

          <el-table
            :data="historyItems"
            v-loading="historyLoading"
            style="width: 100%"
          >
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column label="类型" width="120">
              <template #default="{ row }">
                <el-tag size="small">
                  {{ formatHistoryType(row.type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="experiment_id" label="模型 ID" width="100" />
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="getStatusTag(row.status)" size="small">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="输入" min-width="220">
              <template #default="{ row }">
                <el-tooltip
                  effect="dark"
                  :content="JSON.stringify(row.input_data, null, 2)"
                  placement="top"
                >
                  <span class="mono-text">
                    {{ formatInputSummary(row.input_data) }}
                  </span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column label="创建时间" min-width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>

          <div class="history-pagination">
            <el-pagination
              v-model:current-page="historyQuery.page"
              v-model:page-size="historyQuery.page_size"
              :total="historyTotal"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              @current-change="fetchHistory"
              @size-change="handleHistoryPageSizeChange"
            />
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import predictionsApi, { 
  type PredictionResponse, 
  type TaskStatusResponse,
  type DrugRecommendationResponse,
  type DiseaseRecommendationResponse,
  type PredictionHistoryItem,
  type PredictionHistoryResponse,
} from '@/api/predictions'
import { listDatasets, type Dataset } from '@/api/datasets'
import { listExperiments, getActiveModel, type Experiment } from '@/api/experiments'

// Tabs
const activeTab = ref('single')

// Data
const datasets = ref<Dataset[]>([])
const completedModels = ref<Experiment[]>([])
const activeModel = ref<Experiment | null>(null)

// Single Prediction
const singleFormRef = ref<FormInstance>()
const singleLoading = ref(false)
const singleResult = ref<PredictionResponse | null>(null)
const singleForm = reactive({
  drug_id: '',
  disease_id: '',
  model_id: undefined as number | undefined
})
const singleRules = reactive<FormRules>({
  drug_id: [{ required: true, message: '请输入药物 ID', trigger: 'blur' }],
  disease_id: [{ required: true, message: '请输入疾病 ID', trigger: 'blur' }]
})

// Batch Prediction
const batchFormRef = ref<FormInstance>()
const batchLoading = ref(false)
const batchForm = reactive({
  dataset_id: undefined as number | undefined,
  model_id: undefined as number | undefined
})
const batchRules = reactive<FormRules>({
  dataset_id: [{ required: true, message: '请选择数据集', trigger: 'change' }]
})

interface BatchTask extends TaskStatusResponse {
  timer?: any;
}
const batchTasks = ref<BatchTask[]>([])

// Recommendation
const recommendMode = ref<'disease_to_drugs' | 'drug_to_diseases'>('disease_to_drugs')
const recommendLoading = ref(false)
const recommendForm = reactive({
  disease_id: '',
  drug_id: '',
  top_k: 10,
  model_id: undefined as number | undefined
})
const drugRecommend = ref<DrugRecommendationResponse | null>(null)
const diseaseRecommend = ref<DiseaseRecommendationResponse | null>(null)

const recommendItems = computed(() => {
  if (recommendMode.value === 'disease_to_drugs') {
    return drugRecommend.value?.items ?? []
  }
  return diseaseRecommend.value?.items ?? []
})

// History
const historyLoading = ref(false)
const historyItems = ref<PredictionHistoryItem[]>([])
const historyTotal = ref(0)
const historyQuery = reactive({
  page: 1,
  page_size: 10,
  type: '' as string | '',
  experiment_id: undefined as number | undefined
})

// Methods
const fetchInitialData = async () => {
  try {
    const [dsRes, expRes, activeRes] = await Promise.all([
      listDatasets(1, 100),
      listExperiments(1, 100, { status: 'completed' }),
      getActiveModel()
    ])
    
    datasets.value = dsRes.data.items
    completedModels.value = expRes.data.items
    activeModel.value = activeRes.data
  } catch (error) {
    console.error('Failed to fetch initial data', error)
    ElMessage.error('获取初始数据失败')
  }
}

const handleSinglePredict = async () => {
  if (!singleFormRef.value) return
  
  await singleFormRef.value.validate(async (valid) => {
    if (valid) {
      singleLoading.value = true
      try {
        const res = await predictionsApi.predictSingle(singleForm)
        singleResult.value = res.data
        ElMessage.success('预测完成')
      } catch (error: any) {
        ElMessage.error(error.response?.data?.message || '预测失败')
      } finally {
        singleLoading.value = false
      }
    }
  })
}

const resetSingleForm = () => {
  if (singleFormRef.value) {
    singleFormRef.value.resetFields()
    singleResult.value = null
  }
}

const handleBatchPredict = async () => {
  if (!batchFormRef.value) return
  
  await batchFormRef.value.validate(async (valid) => {
    if (valid) {
      batchLoading.value = true
      try {
        const res = await predictionsApi.predictBatch(batchForm)
        const taskId = res.data.task_id
        
        const newTask: BatchTask = {
          task_id: taskId,
          status: 'PENDING',
          progress: 0,
          message: '等待任务开始...'
        }
        
        batchTasks.value.unshift(newTask)
        startPolling(newTask)
        ElMessage.success('批量预测任务已提交')
      } catch (error: any) {
        ElMessage.error(error.response?.data?.message || '提交失败')
      } finally {
        batchLoading.value = false
      }
    }
  })
}

const startPolling = (task: BatchTask) => {
  task.timer = setInterval(async () => {
    try {
      const res = await predictionsApi.getTaskStatus(task.task_id)
      const data = res.data
      
      task.status = data.status
      task.progress = data.progress
      task.message = data.message
      task.result = data.result
      
      if (data.status === 'SUCCESS' || data.status === 'FAILURE') {
        clearInterval(task.timer)
      }
    } catch (error) {
      console.error('Polling error', error)
      clearInterval(task.timer)
    }
  }, 2000)
}

const getStatusTag = (status: string) => {
  switch (status) {
    case 'PENDING': return 'info'
    case 'PROGRESS': return 'primary'
    case 'SUCCESS': return 'success'
    case 'FAILURE': return 'danger'
    default: return 'info'
  }
}

const getProgressColor = (prob: number) => {
  if (prob > 0.8) return '#67C23A'
  if (prob > 0.5) return '#E6A23C'
  return '#F56C6C'
}

const downloadResults = (filename: string) => {
  const url = predictionsApi.getDownloadUrl(filename)
  window.open(url, '_blank')
}

const handleRecommend = async () => {
  if (recommendMode.value === 'disease_to_drugs' && !recommendForm.disease_id) {
    ElMessage.warning('请输入疾病 ID')
    return
  }
  if (recommendMode.value === 'drug_to_diseases' && !recommendForm.drug_id) {
    ElMessage.warning('请输入药物 ID')
    return
  }

  recommendLoading.value = true
  try {
    if (recommendMode.value === 'disease_to_drugs') {
      const res = await predictionsApi.recommendDrugs({
        disease_id: recommendForm.disease_id,
        top_k: recommendForm.top_k,
        model_id: recommendForm.model_id
      })
      drugRecommend.value = res.data
      diseaseRecommend.value = null
    } else {
      const res = await predictionsApi.recommendDiseases({
        drug_id: recommendForm.drug_id,
        top_k: recommendForm.top_k,
        model_id: recommendForm.model_id
      })
      diseaseRecommend.value = res.data
      drugRecommend.value = null
    }
    ElMessage.success('获取推荐成功')
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.message || '获取推荐失败')
  } finally {
    recommendLoading.value = false
  }
}

const resetRecommend = () => {
  recommendForm.disease_id = ''
  recommendForm.drug_id = ''
  recommendForm.top_k = 10
  recommendForm.model_id = undefined
  drugRecommend.value = null
  diseaseRecommend.value = null
}

const formatHistoryType = (type: string) => {
  switch (type) {
    case 'single':
      return '单例预测'
    case 'batch':
      return '批量预测'
    case 'recommendation':
      return '推荐'
    default:
      return type
  }
}

const formatDateTime = (value: string | undefined) => {
  if (!value) return ''
  try {
    return new Date(value).toLocaleString()
  } catch {
    return value
  }
}

const formatInputSummary = (input: Record<string, any>) => {
  if (!input) return ''
  if (input.mode === 'disease_to_drugs') {
    return `疾病: ${input.disease_id} · Top-${input.top_k}`
  }
  if (input.mode === 'drug_to_diseases') {
    return `药物: ${input.drug_id} · Top-${input.top_k}`
  }
  if (input.drug_id && input.disease_id) {
    return `药物: ${input.drug_id}, 疾病: ${input.disease_id}`
  }
  return JSON.stringify(input)
}

const fetchHistory = async () => {
  historyLoading.value = true
  try {
    const res = await predictionsApi.getHistory({
      page: historyQuery.page,
      page_size: historyQuery.page_size,
      type: historyQuery.type || undefined,
      experiment_id: historyQuery.experiment_id
    })
    const data: PredictionHistoryResponse = res.data
    historyItems.value = data.items
    historyTotal.value = data.total
  } catch (error) {
    console.error('Failed to fetch history', error)
    ElMessage.error('获取预测历史失败')
  } finally {
    historyLoading.value = false
  }
}

const handleHistoryFilterChange = () => {
  historyQuery.page = 1
  fetchHistory()
}

const handleHistoryPageSizeChange = () => {
  historyQuery.page = 1
  fetchHistory()
}

onMounted(() => {
  fetchInitialData()
})

watch(activeTab, (tab) => {
  if (tab === 'history') {
    fetchHistory()
  }
})

onUnmounted(() => {
  batchTasks.value.forEach(task => {
    if (task.timer) clearInterval(task.timer)
  })
})
</script>

<style lang="scss" scoped>
.prediction {
  max-width: 1200px;
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

.prediction-tabs {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.tab-card {
  border: none;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.prediction-form {
  max-width: 600px;
  margin-top: 20px;
}

.mt-4 {
  margin-top: 24px;
}

.task-message {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.history-filters {
  display: flex;
  align-items: center;
  gap: 8px;
}

.history-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.mono-text {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
  font-size: 12px;
}
</style>
