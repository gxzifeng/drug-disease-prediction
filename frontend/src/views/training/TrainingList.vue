<template>
  <div class="training-list fade-in">
    <div class="page-header">
      <h1>模型训练</h1>
      <p>训练表示学习模型（Node2Vec / GCN）</p>
    </div>

    <!-- Action Bar -->
    <div class="action-bar">
      <div class="filters">
        <el-input
          v-model="filters.keyword"
          placeholder="搜索名称..."
          prefix-icon="Search"
          clearable
          style="width: 200px"
          @input="handleSearch"
        />
        <el-select
          v-model="filters.algorithm"
          placeholder="算法类型"
          clearable
          style="width: 140px"
          @change="fetchEmbeddings"
        >
          <el-option label="Node2Vec" value="node2vec" />
          <el-option label="GCN" value="gcn" />
        </el-select>
        <el-select
          v-model="filters.status"
          placeholder="状态"
          clearable
          style="width: 120px"
          @change="fetchEmbeddings"
        >
          <el-option label="待训练" value="pending" />
          <el-option label="训练中" value="running" />
          <el-option label="已完成" value="completed" />
          <el-option label="失败" value="failed" />
        </el-select>
      </div>
      <el-button type="primary" :icon="Plus" @click="showTrainDialog">
        新建训练
      </el-button>
    </div>

    <!-- Embedding List -->
    <el-table
      v-loading="loading"
      :data="embeddings"
      stripe
      style="width: 100%"
      @row-click="handleRowClick"
    >
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="名称" min-width="150">
        <template #default="{ row }">
          <el-link type="primary" :underline="false">{{ row.name }}</el-link>
        </template>
      </el-table-column>
      <el-table-column prop="algorithm" label="算法" width="100">
        <template #default="{ row }">
          <el-tag :type="row.algorithm === 'node2vec' ? 'primary' : 'success'" size="small">
            {{ row.algorithm === 'node2vec' ? 'Node2Vec' : 'GCN' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="embedding_dim" label="维度" width="80" />
      <el-table-column prop="epochs" label="Epochs" width="80" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="small">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="progress" label="进度" width="120">
        <template #default="{ row }">
          <el-progress
            :percentage="row.progress"
            :status="row.status === 'completed' ? 'success' : row.status === 'failed' ? 'exception' : undefined"
            :stroke-width="6"
          />
        </template>
      </el-table-column>
      <el-table-column prop="training_loss" label="训练损失" width="100">
        <template #default="{ row }">
          {{ row.training_loss?.toFixed(4) || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="val_loss" label="验证损失" width="100">
        <template #default="{ row }">
          {{ row.val_loss?.toFixed(4) || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="160">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button
            type="primary"
            link
            size="small"
            @click.stop="viewDetail(row)"
          >
            详情
          </el-button>
          <el-button
            type="danger"
            link
            size="small"
            @click.stop="handleDelete(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Pagination -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchEmbeddings"
        @current-change="fetchEmbeddings"
      />
    </div>

    <!-- Train Dialog -->
    <el-dialog
      v-model="trainDialogVisible"
      title="新建训练任务"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form ref="trainFormRef" :model="trainForm" :rules="trainRules" label-width="100px">
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="trainForm.name" placeholder="请输入训练任务名称" />
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input v-model="trainForm.description" type="textarea" :rows="2" placeholder="可选描述" />
        </el-form-item>
        
        <el-form-item label="选择图" prop="graph_id">
          <el-select v-model="trainForm.graph_id" placeholder="选择要训练的图" style="width: 100%">
            <el-option
              v-for="graph in availableGraphs"
              :key="graph.id"
              :label="`${graph.name} (${graph.num_total_nodes}节点, ${graph.num_edges}边)`"
              :value="graph.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="算法类型" prop="algorithm">
          <el-radio-group v-model="trainForm.algorithm">
            <el-radio-button value="node2vec">Node2Vec</el-radio-button>
            <el-radio-button value="gcn">GCN</el-radio-button>
          </el-radio-group>
        </el-form-item>
        
        <el-divider content-position="left">通用参数</el-divider>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="嵌入维度" prop="embedding_dim">
              <el-input-number v-model="trainForm.embedding_dim" :min="16" :max="512" :step="16" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="训练轮数" prop="epochs">
              <el-input-number v-model="trainForm.epochs" :min="1" :max="1000" :step="10" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="学习率" prop="learning_rate">
              <el-input-number v-model="trainForm.learning_rate" :min="0.0001" :max="1" :step="0.001" :precision="4" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="随机种子" prop="random_seed">
              <el-input-number v-model="trainForm.random_seed" :min="0" :max="99999" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <!-- Node2Vec Parameters -->
        <template v-if="trainForm.algorithm === 'node2vec'">
          <el-divider content-position="left">Node2Vec 参数</el-divider>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="游走长度">
                <el-input-number v-model="trainForm.node2vec_params.walk_length" :min="10" :max="200" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="游走次数">
                <el-input-number v-model="trainForm.node2vec_params.num_walks" :min="1" :max="50" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="参数 p">
                <el-input-number v-model="trainForm.node2vec_params.p" :min="0.1" :max="10" :step="0.1" :precision="1" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="参数 q">
                <el-input-number v-model="trainForm.node2vec_params.q" :min="0.1" :max="10" :step="0.1" :precision="1" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="窗口大小">
                <el-input-number v-model="trainForm.node2vec_params.window_size" :min="2" :max="20" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
        </template>
        
        <!-- GCN Parameters -->
        <template v-if="trainForm.algorithm === 'gcn'">
          <el-divider content-position="left">GCN 参数</el-divider>
          
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="隐藏层维度">
                <el-input-number v-model="trainForm.gcn_params.hidden_channels" :min="16" :max="512" :step="16" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="层数">
                <el-input-number v-model="trainForm.gcn_params.num_layers" :min="1" :max="5" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="Dropout">
                <el-input-number v-model="trainForm.gcn_params.dropout" :min="0" :max="0.9" :step="0.1" :precision="1" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
        </template>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer-tip">
          <el-text type="info" size="small">训练可能需要数分钟，请勿关闭页面，提交后请耐心等待。</el-text>
        </div>
        <el-button @click="trainDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleTrain">
          开始训练
        </el-button>
      </template>
    </el-dialog>

    <!-- Detail Dialog -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="selectedEmbedding?.name || '训练详情'"
      width="900px"
    >
      <template v-if="selectedEmbedding">
        <el-tabs v-model="activeTab">
          <!-- Basic Info Tab -->
          <el-tab-pane label="基本信息" name="info">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="ID">{{ selectedEmbedding.id }}</el-descriptions-item>
              <el-descriptions-item label="名称">{{ selectedEmbedding.name }}</el-descriptions-item>
              <el-descriptions-item label="算法">
                <el-tag :type="selectedEmbedding.algorithm === 'node2vec' ? 'primary' : 'success'">
                  {{ selectedEmbedding.algorithm === 'node2vec' ? 'Node2Vec' : 'GCN' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="getStatusType(selectedEmbedding.status)">
                  {{ getStatusText(selectedEmbedding.status) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="图 ID">{{ selectedEmbedding.graph_id }}</el-descriptions-item>
              <el-descriptions-item label="嵌入维度">{{ selectedEmbedding.embedding_dim }}</el-descriptions-item>
              <el-descriptions-item label="训练轮数">{{ selectedEmbedding.epochs }}</el-descriptions-item>
              <el-descriptions-item label="学习率">{{ selectedEmbedding.learning_rate }}</el-descriptions-item>
              <el-descriptions-item label="随机种子">{{ selectedEmbedding.random_seed }}</el-descriptions-item>
              <el-descriptions-item label="进度">
                <el-progress :percentage="selectedEmbedding.progress" :stroke-width="6" />
              </el-descriptions-item>
              <el-descriptions-item label="训练损失">
                {{ selectedEmbedding.training_loss?.toFixed(6) || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="验证损失">
                {{ selectedEmbedding.val_loss?.toFixed(6) || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="训练时间">
                {{ selectedEmbedding.training_time_seconds ? `${selectedEmbedding.training_time_seconds.toFixed(2)}s` : '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">
                {{ formatDate(selectedEmbedding.created_at) }}
              </el-descriptions-item>
            </el-descriptions>
            
            <!-- Algorithm Specific Parameters -->
            <div v-if="selectedEmbedding.node2vec_params" class="params-section">
              <h4>Node2Vec 参数</h4>
              <el-descriptions :column="3" border size="small">
                <el-descriptions-item label="游走长度">{{ selectedEmbedding.node2vec_params.walk_length }}</el-descriptions-item>
                <el-descriptions-item label="游走次数">{{ selectedEmbedding.node2vec_params.num_walks }}</el-descriptions-item>
                <el-descriptions-item label="窗口大小">{{ selectedEmbedding.node2vec_params.window_size }}</el-descriptions-item>
                <el-descriptions-item label="参数 p">{{ selectedEmbedding.node2vec_params.p }}</el-descriptions-item>
                <el-descriptions-item label="参数 q">{{ selectedEmbedding.node2vec_params.q }}</el-descriptions-item>
              </el-descriptions>
            </div>
            
            <div v-if="selectedEmbedding.gcn_params" class="params-section">
              <h4>GCN 参数</h4>
              <el-descriptions :column="3" border size="small">
                <el-descriptions-item label="隐藏层维度">{{ selectedEmbedding.gcn_params.hidden_channels }}</el-descriptions-item>
                <el-descriptions-item label="层数">{{ selectedEmbedding.gcn_params.num_layers }}</el-descriptions-item>
                <el-descriptions-item label="Dropout">{{ selectedEmbedding.gcn_params.dropout }}</el-descriptions-item>
              </el-descriptions>
            </div>
            
            <div v-if="selectedEmbedding.error_message" class="error-section">
              <el-alert type="error" :title="selectedEmbedding.error_message" :closable="false" show-icon />
            </div>
          </el-tab-pane>
          
          <!-- Training Curve Tab -->
          <el-tab-pane label="训练曲线" name="curve">
            <div v-if="trainingHistory && trainingHistory.epochs.length > 0" class="chart-container">
              <v-chart :option="chartOption" autoresize style="height: 400px" />
            </div>
            <el-empty v-else description="暂无训练历史数据" />
          </el-tab-pane>
        </el-tabs>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import dayjs from 'dayjs'

import {
  listEmbeddings,
  trainEmbedding,
  getEmbedding,
  getTrainingHistory,
  deleteEmbedding,
  Embedding,
  EmbeddingFilter,
  EmbeddingTrainRequest,
  TrainingHistory,
} from '@/api/embeddings'
import { listGraphs, Graph } from '@/api/graphs'
import { getAppSettings } from '@/utils/settings'

// Register ECharts components
use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
])

// State
const loading = ref(false)
const submitting = ref(false)
const embeddings = ref<Embedding[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const filters = reactive<EmbeddingFilter>({
  keyword: '',
  algorithm: undefined,
  status: undefined,
})

// Dialog state
const trainDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const trainFormRef = ref<FormInstance>()
const selectedEmbedding = ref<Embedding | null>(null)
const trainingHistory = ref<TrainingHistory | null>(null)
const activeTab = ref('info')
const availableGraphs = ref<Graph[]>([])

// Train form
const defaultTrainForm = (): EmbeddingTrainRequest & { node2vec_params: Required<EmbeddingTrainRequest['node2vec_params']>; gcn_params: Required<EmbeddingTrainRequest['gcn_params']> } => ({
  graph_id: 0,
  name: '',
  description: '',
  algorithm: 'node2vec',
  embedding_dim: 64,
  epochs: 100,
  learning_rate: 0.01,
  random_seed: 42,
  node2vec_params: {
    walk_length: 80,
    num_walks: 10,
    p: 1.0,
    q: 1.0,
    window_size: 5,
  },
  gcn_params: {
    hidden_channels: 64,
    num_layers: 2,
    dropout: 0.5,
  },
})

const trainForm = reactive(defaultTrainForm())

const trainRules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  graph_id: [{ required: true, message: '请选择图', trigger: 'change' }],
  algorithm: [{ required: true, message: '请选择算法', trigger: 'change' }],
}

// Computed
const chartOption = computed(() => {
  if (!trainingHistory.value || trainingHistory.value.epochs.length === 0) {
    return {}
  }

  const series: any[] = [
    {
      name: '训练损失',
      type: 'line',
      data: trainingHistory.value.train_losses,
      smooth: true,
      symbol: 'circle',
      symbolSize: 4,
      lineStyle: { width: 2 },
    },
  ]

  if (trainingHistory.value.val_losses && trainingHistory.value.val_losses.length > 0) {
    series.push({
      name: '验证损失',
      type: 'line',
      data: trainingHistory.value.val_losses,
      smooth: true,
      symbol: 'circle',
      symbolSize: 4,
      lineStyle: { width: 2 },
    })
  }

  return {
    title: {
      text: '训练曲线',
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
    },
    legend: {
      data: ['训练损失', '验证损失'],
      top: 30,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      name: 'Epoch',
      data: trainingHistory.value.epochs,
      boundaryGap: false,
    },
    yAxis: {
      type: 'value',
      name: 'Loss',
      min: 0,
    },
    series,
  }
})

// Methods
const formatDate = (dateStr: string) => {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '待训练',
    running: '训练中',
    completed: '已完成',
    failed: '失败',
  }
  return texts[status] || status
}

let searchTimer: ReturnType<typeof setTimeout> | null = null
const handleSearch = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    fetchEmbeddings()
  }, 300)
}

const fetchEmbeddings = async () => {
  loading.value = true
  try {
    const response = await listEmbeddings(currentPage.value, pageSize.value, {
      keyword: filters.keyword || undefined,
      algorithm: filters.algorithm || undefined,
      status: filters.status || undefined,
    })
    embeddings.value = response.data.items
    total.value = response.data.total
  } catch (error) {
    console.error('Failed to fetch embeddings:', error)
  } finally {
    loading.value = false
  }
}

const fetchGraphs = async () => {
  try {
    const response = await listGraphs(1, 100, { is_built: true })
    availableGraphs.value = response.data.items
  } catch (error) {
    console.error('Failed to fetch graphs:', error)
  }
}

const showTrainDialog = async () => {
  await fetchGraphs()
  if (availableGraphs.value.length === 0) {
    ElMessage.warning('请先构建图再进行训练')
    return
  }
  Object.assign(trainForm, defaultTrainForm())
  // 使用系统设置中的默认参数（若有）
  const appSettings = getAppSettings()
  trainForm.embedding_dim = appSettings.embeddingDim
  trainForm.learning_rate = appSettings.learningRate
  trainForm.random_seed = appSettings.randomSeed
  // 默认选中第一个可用图，避免出现 graph_id=0 的困惑
  trainForm.graph_id = availableGraphs.value[0].id
  trainDialogVisible.value = true
}

const handleTrain = async () => {
  if (!trainFormRef.value) return
  
  try {
    await trainFormRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    const request: EmbeddingTrainRequest = {
      graph_id: trainForm.graph_id,
      name: trainForm.name,
      description: trainForm.description || undefined,
      algorithm: trainForm.algorithm,
      embedding_dim: trainForm.embedding_dim,
      epochs: trainForm.epochs,
      learning_rate: trainForm.learning_rate,
      random_seed: trainForm.random_seed,
    }

    if (trainForm.algorithm === 'node2vec') {
      request.node2vec_params = { ...trainForm.node2vec_params }
    } else {
      request.gcn_params = { ...trainForm.gcn_params }
    }

    await trainEmbedding(request)
    ElMessage.success('训练任务已创建')
    trainDialogVisible.value = false
    fetchEmbeddings()
  } catch (error) {
    console.error('Failed to create training:', error)
  } finally {
    submitting.value = false
  }
}

const handleRowClick = (row: Embedding) => {
  viewDetail(row)
}

const viewDetail = async (embedding: Embedding) => {
  selectedEmbedding.value = embedding
  activeTab.value = 'info'
  detailDialogVisible.value = true

  // Fetch training history
  if (embedding.status === 'completed' || embedding.status === 'running') {
    try {
      const response = await getTrainingHistory(embedding.id)
      trainingHistory.value = response.data
    } catch (error) {
      console.error('Failed to fetch training history:', error)
      trainingHistory.value = null
    }
  } else {
    trainingHistory.value = null
  }
}

const handleDelete = async (embedding: Embedding) => {
  try {
    const isRunning = embedding.status === 'running'
    const message = isRunning
      ? `任务「${embedding.name}」正在训练中。删除后该记录会移除，后台训练可能仍在进行但结果将不再保留。确定删除？`
      : `确定要删除训练任务「${embedding.name}」吗？此操作不可恢复。`
    await ElMessageBox.confirm(
      message,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await deleteEmbedding(embedding.id)
    ElMessage.success('删除成功')
    fetchEmbeddings()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Failed to delete embedding:', error)
      const errorMsg = error?.response?.data?.message || error?.message || '删除失败，请检查网络连接或登录状态'
      ElMessage.error(`删除失败: ${errorMsg}`)
    }
  }
}

// Lifecycle
onMounted(() => {
  fetchEmbeddings()
})

// Watch for tab changes to refresh chart
watch(activeTab, (newTab) => {
  if (newTab === 'curve' && selectedEmbedding.value) {
    // Chart will auto-resize
  }
})
</script>

<style lang="scss" scoped>
.dialog-footer-tip {
  margin-bottom: 12px;
}

.training-list {
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

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  .filters {
    display: flex;
    gap: 12px;
  }
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  padding: 12px 0;
}

.params-section {
  margin-top: 20px;

  h4 {
    margin-bottom: 12px;
    color: var(--text-primary);
    font-weight: 500;
  }
}

.error-section {
  margin-top: 20px;
}

.chart-container {
  padding: 20px 0;
}

:deep(.el-descriptions__label) {
  width: 100px;
}
</style>
