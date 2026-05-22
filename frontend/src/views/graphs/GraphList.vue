<template>
  <div class="graph-list fade-in">
    <div class="page-header">
      <div class="header-left">
        <h1>网络构建</h1>
        <p>从数据集构建药物-疾病关联网络</p>
      </div>
      <div class="header-right">
        <el-button type="primary" :icon="Plus" @click="showBuildDialog = true">
          构建网络
        </el-button>
      </div>
    </div>

    <!-- Filters -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="搜索网络名称" clearable />
        </el-form-item>
        <el-form-item label="数据集">
          <el-select v-model="filters.dataset_id" placeholder="选择数据集" clearable>
            <el-option
              v-for="ds in availableDatasets"
              :key="ds.id"
              :label="ds.name"
              :value="ds.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.is_built" placeholder="选择状态" clearable>
            <el-option label="已构建" :value="true" />
            <el-option label="构建失败" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Statistics Cards -->
    <div class="stats-row" v-if="graphs.length > 0">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-value">{{ pagination.total }}</div>
          <div class="stat-label">网络总数</div>
        </div>
        <el-icon class="stat-icon"><Share /></el-icon>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-value">{{ totalStats.nodes.toLocaleString() }}</div>
          <div class="stat-label">节点总数</div>
        </div>
        <el-icon class="stat-icon"><DataBoard /></el-icon>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-value">{{ totalStats.edges.toLocaleString() }}</div>
          <div class="stat-label">边总数</div>
        </div>
        <el-icon class="stat-icon"><Connection /></el-icon>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-value">{{ builtCount }}</div>
          <div class="stat-label">已构建</div>
        </div>
        <el-icon class="stat-icon"><CircleCheck /></el-icon>
      </el-card>
    </div>

    <!-- Graph Table -->
    <el-card class="table-card">
      <el-table :data="graphs" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="名称" min-width="180">
          <template #default="{ row }">
            <div class="graph-name">
              <el-icon><Share /></el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="num_total_nodes" label="节点数" width="100">
          <template #default="{ row }">
            {{ row.num_total_nodes.toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column label="节点分布" width="150">
          <template #default="{ row }">
            <el-tooltip :content="`药物: ${row.num_drug_nodes}, 疾病: ${row.num_disease_nodes}`">
              <div class="node-distribution">
                <span class="drug-count">{{ row.num_drug_nodes }}</span>
                <span class="separator">/</span>
                <span class="disease-count">{{ row.num_disease_nodes }}</span>
              </div>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="num_edges" label="边数" width="100">
          <template #default="{ row }">
            {{ row.num_edges.toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column label="正/负边" width="120">
          <template #default="{ row }">
            <el-tooltip :content="`正样本: ${row.num_positive_edges}, 负样本: ${row.num_negative_edges}`">
              <div class="edge-ratio">
                <span class="positive">{{ row.num_positive_edges }}</span>
                <span class="separator">/</span>
                <span class="negative">{{ row.num_negative_edges }}</span>
              </div>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="数据划分" width="160">
          <template #default="{ row }">
            <el-tooltip :content="`训练: ${row.num_train_edges}, 验证: ${row.num_val_edges}, 测试: ${row.num_test_edges}`">
              <div class="split-info">
                <span>{{ row.num_train_edges }}</span>
                <span>/</span>
                <span>{{ row.num_val_edges }}</span>
                <span>/</span>
                <span>{{ row.num_test_edges }}</span>
              </div>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="is_built" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_built ? 'success' : 'danger'" size="small">
              {{ row.is_built ? '已构建' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" @click="handleViewSummary(row)" :disabled="!row.is_built">
              详情
            </el-button>
            <el-button text type="primary" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button text type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- Empty State -->
    <el-empty v-if="!loading && graphs.length === 0" description="暂无网络数据" class="empty-state">
      <el-button type="primary" @click="showBuildDialog = true">
        构建第一个网络
      </el-button>
    </el-empty>

    <!-- Build Graph Dialog -->
    <el-dialog
      v-model="showBuildDialog"
      title="构建网络"
      width="600px"
      destroy-on-close
    >
      <el-form :model="buildForm" :rules="buildRules" ref="buildFormRef" label-width="120px">
        <el-form-item label="网络名称" prop="name">
          <el-input v-model="buildForm.name" placeholder="请输入网络名称" />
        </el-form-item>
        <el-form-item label="数据集" prop="dataset_id">
          <el-select v-model="buildForm.dataset_id" placeholder="选择数据集" style="width: 100%">
            <el-option
              v-for="ds in availableDatasets"
              :key="ds.id"
              :label="`${ds.name} (${ds.drug_count}药物, ${ds.disease_count}疾病)`"
              :value="ds.id"
            />
          </el-select>
        </el-form-item>
        
        <el-divider content-position="left">构图参数</el-divider>
        
        <el-form-item label="负采样比例" prop="negative_sample_ratio">
          <el-input-number
            v-model="buildForm.negative_sample_ratio"
            :min="0.1"
            :max="10"
            :step="0.1"
            :precision="1"
          />
          <span class="form-hint">负样本与正样本的比例</span>
        </el-form-item>
        
        <el-form-item label="数据划分" required>
          <div class="split-inputs">
            <div class="split-item">
              <span class="split-label">训练集</span>
              <el-input-number
                v-model="buildForm.train_ratio"
                :min="0.1"
                :max="0.9"
                :step="0.05"
                :precision="2"
                size="small"
              />
            </div>
            <div class="split-item">
              <span class="split-label">验证集</span>
              <el-input-number
                v-model="buildForm.val_ratio"
                :min="0.05"
                :max="0.4"
                :step="0.05"
                :precision="2"
                size="small"
              />
            </div>
            <div class="split-item">
              <span class="split-label">测试集</span>
              <el-input-number
                v-model="buildForm.test_ratio"
                :min="0.05"
                :max="0.4"
                :step="0.05"
                :precision="2"
                size="small"
              />
            </div>
          </div>
          <div class="split-total" :class="{ 'is-error': !isRatioValid }">
            总计: {{ splitTotal.toFixed(2) }}
            <span v-if="!isRatioValid" class="error-hint">(需等于 1.00)</span>
          </div>
        </el-form-item>
        
        <el-form-item label="随机种子" prop="random_seed">
          <el-input-number
            v-model="buildForm.random_seed"
            :min="0"
            :max="999999"
            :step="1"
          />
          <span class="form-hint">用于复现结果</span>
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="buildForm.description"
            type="textarea"
            :rows="2"
            placeholder="请输入网络描述（可选）"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showBuildDialog = false">取消</el-button>
        <el-button type="primary" @click="handleBuild" :loading="building" :disabled="!isRatioValid">
          {{ building ? '构建中...' : '开始构建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Summary Dialog -->
    <el-dialog
      v-model="showSummaryDialog"
      :title="`网络详情 - ${currentSummary?.name || ''}`"
      width="700px"
    >
      <div class="summary-content" v-loading="summaryLoading">
        <template v-if="currentSummary">
          <!-- Basic Info -->
          <div class="summary-section">
            <h4>基本信息</h4>
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="网络ID">{{ currentSummary.id }}</el-descriptions-item>
              <el-descriptions-item label="网络名称">{{ currentSummary.name }}</el-descriptions-item>
              <el-descriptions-item label="源数据集">{{ currentSummary.dataset_name }}</el-descriptions-item>
              <el-descriptions-item label="创建时间">{{ formatDateTime(currentSummary.created_at) }}</el-descriptions-item>
            </el-descriptions>
          </div>
          
          <!-- Node Statistics -->
          <div class="summary-section">
            <h4>节点统计</h4>
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-item-value">{{ currentSummary.num_drug_nodes.toLocaleString() }}</div>
                <div class="stat-item-label">药物节点</div>
              </div>
              <div class="stat-item">
                <div class="stat-item-value">{{ currentSummary.num_disease_nodes.toLocaleString() }}</div>
                <div class="stat-item-label">疾病节点</div>
              </div>
              <div class="stat-item highlight">
                <div class="stat-item-value">{{ currentSummary.num_total_nodes.toLocaleString() }}</div>
                <div class="stat-item-label">总节点数</div>
              </div>
            </div>
          </div>
          
          <!-- Edge Statistics -->
          <div class="summary-section">
            <h4>边统计</h4>
            <div class="stats-grid">
              <div class="stat-item positive">
                <div class="stat-item-value">{{ currentSummary.num_positive_edges.toLocaleString() }}</div>
                <div class="stat-item-label">正样本边</div>
              </div>
              <div class="stat-item negative">
                <div class="stat-item-value">{{ currentSummary.num_negative_edges.toLocaleString() }}</div>
                <div class="stat-item-label">负样本边</div>
              </div>
              <div class="stat-item highlight">
                <div class="stat-item-value">{{ currentSummary.num_edges.toLocaleString() }}</div>
                <div class="stat-item-label">总边数</div>
              </div>
            </div>
            <div class="ratio-bar">
              <div 
                class="positive-bar" 
                :style="{ width: `${currentSummary.positive_ratio * 100}%` }"
              >
                {{ (currentSummary.positive_ratio * 100).toFixed(1) }}%
              </div>
              <div 
                class="negative-bar" 
                :style="{ width: `${(1 - currentSummary.positive_ratio) * 100}%` }"
              >
                {{ ((1 - currentSummary.positive_ratio) * 100).toFixed(1) }}%
              </div>
            </div>
          </div>
          
          <!-- Split Statistics -->
          <div class="summary-section">
            <h4>数据划分</h4>
            <div class="stats-grid">
              <div class="stat-item train">
                <div class="stat-item-value">{{ currentSummary.num_train_edges.toLocaleString() }}</div>
                <div class="stat-item-label">训练集 ({{ (currentSummary.train_ratio_actual * 100).toFixed(1) }}%)</div>
              </div>
              <div class="stat-item val">
                <div class="stat-item-value">{{ currentSummary.num_val_edges.toLocaleString() }}</div>
                <div class="stat-item-label">验证集 ({{ (currentSummary.val_ratio_actual * 100).toFixed(1) }}%)</div>
              </div>
              <div class="stat-item test">
                <div class="stat-item-value">{{ currentSummary.num_test_edges.toLocaleString() }}</div>
                <div class="stat-item-label">测试集 ({{ (currentSummary.test_ratio_actual * 100).toFixed(1) }}%)</div>
              </div>
            </div>
            <div class="split-bar">
              <div 
                class="train-bar" 
                :style="{ width: `${currentSummary.train_ratio_actual * 100}%` }"
              >训练</div>
              <div 
                class="val-bar" 
                :style="{ width: `${currentSummary.val_ratio_actual * 100}%` }"
              >验证</div>
              <div 
                class="test-bar" 
                :style="{ width: `${currentSummary.test_ratio_actual * 100}%` }"
              >测试</div>
            </div>
          </div>
          
          <!-- Build Parameters -->
          <div class="summary-section">
            <h4>构建参数</h4>
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="负采样比例">{{ currentSummary.negative_sample_ratio }}</el-descriptions-item>
              <el-descriptions-item label="随机种子">{{ currentSummary.random_seed }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </template>
      </div>
      
      <template #footer>
        <el-button @click="showSummaryDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- Edit Dialog -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑网络"
      width="500px"
      destroy-on-close
    >
      <el-form :model="editForm" :rules="editRules" ref="editFormRef" label-width="100px">
        <el-form-item label="网络名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入网络名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入网络描述"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUpdate" :loading="updating">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { Plus, Share, DataBoard, Connection, CircleCheck } from '@element-plus/icons-vue'
import {
  listGraphs,
  buildGraph,
  getGraphSummary,
  updateGraph,
  deleteGraph,
  type Graph,
  type GraphSummary,
} from '@/api/graphs'
import { listDatasets, type Dataset } from '@/api/datasets'

// ============== Route ==============

const route = useRoute()

// ============== State ==============

const loading = ref(false)
const building = ref(false)
const summaryLoading = ref(false)
const updating = ref(false)

const showBuildDialog = ref(false)
const showSummaryDialog = ref(false)
const showEditDialog = ref(false)

const buildFormRef = ref<FormInstance>()
const editFormRef = ref<FormInstance>()

const filters = reactive({
  keyword: '',
  dataset_id: undefined as number | undefined,
  is_built: undefined as boolean | undefined,
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

const buildForm = reactive({
  name: '',
  dataset_id: undefined as number | undefined,
  description: '',
  negative_sample_ratio: 1.0,
  train_ratio: 0.7,
  val_ratio: 0.15,
  test_ratio: 0.15,
  random_seed: 42,
})

const editForm = reactive({
  id: 0,
  name: '',
  description: '',
})

const buildRules = {
  name: [{ required: true, message: '请输入网络名称', trigger: 'blur' }],
  dataset_id: [{ required: true, message: '请选择数据集', trigger: 'change' }],
}

const editRules = {
  name: [{ required: true, message: '请输入网络名称', trigger: 'blur' }],
}

const graphs = ref<Graph[]>([])
const availableDatasets = ref<Dataset[]>([])
const currentSummary = ref<GraphSummary | null>(null)

// ============== Computed ==============

const totalStats = computed(() => ({
  nodes: graphs.value.reduce((sum, g) => sum + g.num_total_nodes, 0),
  edges: graphs.value.reduce((sum, g) => sum + g.num_edges, 0),
}))

const builtCount = computed(() => graphs.value.filter(g => g.is_built).length)

const splitTotal = computed(() => 
  buildForm.train_ratio + buildForm.val_ratio + buildForm.test_ratio
)

const isRatioValid = computed(() => Math.abs(splitTotal.value - 1.0) < 0.001)

// ============== Methods ==============

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const loadGraphs = async () => {
  loading.value = true
  try {
    const response = await listGraphs(pagination.page, pagination.pageSize, {
      keyword: filters.keyword || undefined,
      dataset_id: filters.dataset_id,
      is_built: filters.is_built,
    })
    
    graphs.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    console.error('Failed to load graphs:', error)
  } finally {
    loading.value = false
  }
}

const loadDatasets = async () => {
  try {
    const response = await listDatasets(1, 100)
    availableDatasets.value = response.data.items.filter(d => d.is_parsed)
  } catch (error) {
    console.error('Failed to load datasets:', error)
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadGraphs()
}

const handleReset = () => {
  filters.keyword = ''
  filters.dataset_id = undefined
  filters.is_built = undefined
  handleSearch()
}

const handleSizeChange = () => {
  pagination.page = 1
  loadGraphs()
}

const handlePageChange = () => {
  loadGraphs()
}

const handleBuild = async () => {
  if (!buildFormRef.value) return
  
  const valid = await buildFormRef.value.validate().catch(() => false)
  if (!valid) return
  
  if (!isRatioValid.value) {
    ElMessage.warning('训练/验证/测试集比例之和必须等于 1.0')
    return
  }
  
  building.value = true
  try {
    const response = await buildGraph({
      name: buildForm.name,
      dataset_id: buildForm.dataset_id!,
      description: buildForm.description || undefined,
      negative_sample_ratio: buildForm.negative_sample_ratio,
      train_ratio: buildForm.train_ratio,
      val_ratio: buildForm.val_ratio,
      test_ratio: buildForm.test_ratio,
      random_seed: buildForm.random_seed,
    })
    
    if (response.data.is_built) {
      ElMessage.success('网络构建成功')
    } else {
      ElMessage.error(`网络构建失败: ${response.data.build_error}`)
    }
    
    showBuildDialog.value = false
    
    // Reset form
    buildForm.name = ''
    buildForm.dataset_id = undefined
    buildForm.description = ''
    buildForm.negative_sample_ratio = 1.0
    buildForm.train_ratio = 0.7
    buildForm.val_ratio = 0.15
    buildForm.test_ratio = 0.15
    buildForm.random_seed = 42
    
    loadGraphs()
  } catch (error) {
    console.error('Build failed:', error)
  } finally {
    building.value = false
  }
}

const handleViewSummary = async (row: Graph) => {
  showSummaryDialog.value = true
  summaryLoading.value = true
  
  try {
    const response = await getGraphSummary(row.id)
    currentSummary.value = response.data
  } catch (error) {
    console.error('Failed to load summary:', error)
  } finally {
    summaryLoading.value = false
  }
}

const handleEdit = (row: Graph) => {
  editForm.id = row.id
  editForm.name = row.name
  editForm.description = row.description || ''
  showEditDialog.value = true
}

const handleUpdate = async () => {
  if (!editFormRef.value) return
  
  const valid = await editFormRef.value.validate().catch(() => false)
  if (!valid) return
  
  updating.value = true
  try {
    await updateGraph(editForm.id, {
      name: editForm.name,
      description: editForm.description || undefined,
    })
    
    ElMessage.success('更新成功')
    showEditDialog.value = false
    loadGraphs()
  } catch (error) {
    console.error('Update failed:', error)
  } finally {
    updating.value = false
  }
}

const handleDelete = async (row: Graph) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除网络 "${row.name}" 吗？此操作将删除所有相关文件，不可恢复。`,
      '确认删除',
      { type: 'warning' }
    )
    
    await deleteGraph(row.id)
    ElMessage.success('删除成功')
    loadGraphs()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Delete failed:', error)
    }
  }
}

// ============== Lifecycle ==============

onMounted(async () => {
  await loadDatasets()
  loadGraphs()
  
  // Check for dataset_id query parameter
  const datasetId = route.query.dataset_id
  const datasetName = route.query.dataset_name as string
  
  if (datasetId) {
    const id = parseInt(datasetId as string)
    if (!isNaN(id)) {
      // Pre-select dataset and open build dialog
      buildForm.dataset_id = id
      if (datasetName) {
        buildForm.name = `${datasetName}_graph`
      }
      showBuildDialog.value = true
    }
  }
})
</script>

<style lang="scss" scoped>
.graph-list {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  
  .header-left {
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
}

.filter-card {
  margin-bottom: 24px;
  
  :deep(.el-form-item) {
    margin-bottom: 0;
  }
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  position: relative;
  overflow: hidden;
  
  .stat-content {
    position: relative;
    z-index: 1;
  }
  
  .stat-value {
    font-size: 32px;
    font-weight: 700;
    color: var(--primary-light);
    margin-bottom: 4px;
  }
  
  .stat-label {
    font-size: 14px;
    color: var(--text-secondary);
  }
  
  .stat-icon {
    position: absolute;
    right: 16px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 48px;
    color: var(--primary-light);
    opacity: 0.15;
  }
}

.table-card {
  .graph-name {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .el-icon {
      color: var(--primary-light);
    }
  }
  
  .node-distribution,
  .edge-ratio {
    font-family: monospace;
    
    .separator {
      color: var(--text-secondary);
      margin: 0 4px;
    }
  }
  
  .node-distribution {
    .drug-count { color: var(--el-color-primary); }
    .disease-count { color: var(--el-color-warning); }
  }
  
  .edge-ratio {
    .positive { color: var(--el-color-success); }
    .negative { color: var(--el-color-info); }
  }
  
  .split-info {
    font-family: monospace;
    font-size: 12px;
    color: var(--text-secondary);
    
    span:nth-child(1) { color: #67c23a; }
    span:nth-child(3) { color: #e6a23c; }
    span:nth-child(5) { color: #909399; }
  }
  
  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}

.empty-state {
  margin-top: 60px;
}

// Build Dialog Styles
.split-inputs {
  display: flex;
  gap: 16px;
  
  .split-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    
    .split-label {
      font-size: 12px;
      color: var(--text-secondary);
    }
  }
}

.split-total {
  margin-top: 8px;
  font-size: 13px;
  color: var(--text-secondary);
  
  &.is-error {
    color: var(--el-color-danger);
  }
  
  .error-hint {
    margin-left: 8px;
  }
}

.form-hint {
  margin-left: 12px;
  font-size: 12px;
  color: var(--text-secondary);
}

// Summary Dialog Styles
.summary-content {
  min-height: 300px;
}

.summary-section {
  margin-bottom: 24px;
  
  h4 {
    font-size: 15px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--card-border);
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: var(--card-bg);
  border-radius: 8px;
  border: 1px solid var(--card-border);
  
  .stat-item-value {
    font-size: 24px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 4px;
  }
  
  .stat-item-label {
    font-size: 13px;
    color: var(--text-secondary);
  }
  
  &.highlight {
    background: rgba(var(--primary-rgb), 0.1);
    border-color: var(--primary-light);
    
    .stat-item-value {
      color: var(--primary-light);
    }
  }
  
  &.positive .stat-item-value { color: var(--el-color-success); }
  &.negative .stat-item-value { color: var(--el-color-info); }
  &.train .stat-item-value { color: #67c23a; }
  &.val .stat-item-value { color: #e6a23c; }
  &.test .stat-item-value { color: #909399; }
}

.ratio-bar,
.split-bar {
  display: flex;
  height: 24px;
  border-radius: 4px;
  overflow: hidden;
  font-size: 12px;
  font-weight: 500;
  
  > div {
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    min-width: 40px;
  }
}

.ratio-bar {
  .positive-bar { background: var(--el-color-success); }
  .negative-bar { background: var(--el-color-info); }
}

.split-bar {
  .train-bar { background: #67c23a; }
  .val-bar { background: #e6a23c; }
  .test-bar { background: #909399; }
}
</style>
