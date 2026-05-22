<template>
  <div class="dataset-list fade-in">
    <div class="page-header">
      <div class="header-left">
        <h1>数据管理</h1>
        <p>管理药物-疾病关联数据集</p>
      </div>
      <div class="header-right">
        <el-button type="primary" :icon="Upload" @click="showUploadDialog = true">
          上传数据集
        </el-button>
      </div>
    </div>

    <!-- Filters -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="搜索数据集名称" clearable />
        </el-form-item>
        <el-form-item label="来源">
          <el-select v-model="filters.source" placeholder="选择来源" clearable>
            <el-option label="DrugBank" value="drugbank" />
            <el-option label="CTD" value="ctd" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DDTHH:mm:ss"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Statistics Cards -->
    <div class="stats-row" v-if="datasets.length > 0">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-value">{{ totalStats.datasets }}</div>
          <div class="stat-label">数据集总数</div>
        </div>
        <el-icon class="stat-icon"><FolderOpened /></el-icon>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-value">{{ totalStats.drugs }}</div>
          <div class="stat-label">药物总数</div>
        </div>
        <el-icon class="stat-icon"><Box /></el-icon>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-value">{{ totalStats.diseases }}</div>
          <div class="stat-label">疾病总数</div>
        </div>
        <el-icon class="stat-icon"><FirstAidKit /></el-icon>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-value">{{ totalStats.associations }}</div>
          <div class="stat-label">关联总数</div>
        </div>
        <el-icon class="stat-icon"><Connection /></el-icon>
      </el-card>
    </div>

    <!-- Dataset Table -->
    <el-card class="table-card">
      <el-table :data="datasets" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="名称" min-width="200">
          <template #default="{ row }">
            <div class="dataset-name">
              <el-icon><Document /></el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="120">
          <template #default="{ row }">
            <el-tag :type="getSourceTagType(row.source)">{{ row.source }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="drug_count" label="药物数" width="100" />
        <el-table-column prop="disease_count" label="疾病数" width="100" />
        <el-table-column prop="association_count" label="关联数" width="100" />
        <el-table-column prop="is_parsed" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_parsed ? 'success' : 'danger'" size="small">
              {{ row.is_parsed ? '已解析' : '解析失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" @click="handlePreview(row)">
              预览
            </el-button>
            <el-button text type="primary" @click="handleStats(row)">
              统计
            </el-button>
            <el-button text type="primary" @click="handleBuildGraph(row)">
              构图
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
    <el-empty v-if="!loading && datasets.length === 0" description="暂无数据集" class="empty-state">
      <el-button type="primary" @click="showUploadDialog = true">
        上传第一个数据集
      </el-button>
    </el-empty>

    <!-- Upload Dialog -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传数据集"
      width="600px"
      destroy-on-close
    >
      <el-form :model="uploadForm" :rules="uploadRules" ref="uploadFormRef" label-width="100px">
        <el-form-item label="数据集名称" prop="name">
          <el-input v-model="uploadForm.name" placeholder="请输入数据集名称" />
        </el-form-item>
        <el-form-item label="数据来源" prop="source">
          <el-select v-model="uploadForm.source" placeholder="选择数据来源">
            <el-option label="DrugBank" value="drugbank" />
            <el-option label="CTD" value="ctd" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="数据文件" prop="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".csv,.tsv,.txt"
            drag
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 CSV/TSV 格式，文件大小不超过 100MB<br/>
                必需列: drug_id, disease_id<br/>
                可选列: drug_name, disease_name, label
              </div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="uploadForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入数据集描述（可选）"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUpload" :loading="uploading">
          {{ uploading ? '上传中...' : '上传' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Preview Dialog -->
    <el-dialog
      v-model="showPreviewDialog"
      :title="`数据预览 - ${previewDataset?.name || ''}`"
      width="90%"
      destroy-on-close
    >
      <el-table :data="previewData.records" v-loading="previewLoading" max-height="500">
        <el-table-column prop="drug_id" label="药物ID" width="150" />
        <el-table-column prop="drug_name" label="药物名称" min-width="200">
          <template #default="{ row }">
            {{ row.drug_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="disease_id" label="疾病ID" width="150" />
        <el-table-column prop="disease_name" label="疾病名称" min-width="200">
          <template #default="{ row }">
            {{ row.disease_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="label" label="关联标签" width="100">
          <template #default="{ row }">
            <el-tag :type="row.label === 1 ? 'success' : 'info'" size="small">
              {{ row.label === 1 ? '正关联' : '负关联' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="preview-pagination">
        <el-pagination
          v-model:current-page="previewPagination.page"
          v-model:page-size="previewPagination.pageSize"
          :total="previewPagination.total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="handlePreviewSizeChange"
          @current-change="handlePreviewPageChange"
        />
      </div>
    </el-dialog>

    <!-- Stats Dialog -->
    <el-dialog
      v-model="showStatsDialog"
      :title="`数据统计 - ${statsDataset?.name || ''}`"
      width="600px"
    >
      <div class="stats-dialog-content" v-loading="statsLoading">
        <div class="stats-grid">
          <div class="stats-item">
            <div class="stats-item-label">药物数量</div>
            <div class="stats-item-value">{{ currentStats?.drug_count || 0 }}</div>
          </div>
          <div class="stats-item">
            <div class="stats-item-label">疾病数量</div>
            <div class="stats-item-value">{{ currentStats?.disease_count || 0 }}</div>
          </div>
          <div class="stats-item">
            <div class="stats-item-label">关联总数</div>
            <div class="stats-item-value">{{ currentStats?.association_count || 0 }}</div>
          </div>
          <div class="stats-item">
            <div class="stats-item-label">正样本数</div>
            <div class="stats-item-value positive">{{ currentStats?.positive_count || 0 }}</div>
          </div>
          <div class="stats-item">
            <div class="stats-item-label">负样本数</div>
            <div class="stats-item-value negative">{{ currentStats?.negative_count || 0 }}</div>
          </div>
          <div class="stats-item">
            <div class="stats-item-label">正样本比例</div>
            <div class="stats-item-value">{{ ((currentStats?.positive_ratio || 0) * 100).toFixed(2) }}%</div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type UploadInstance, type UploadFile } from 'element-plus'
import { Upload, Document, UploadFilled, FolderOpened, Box, FirstAidKit, Connection } from '@element-plus/icons-vue'
import {
  listDatasets,
  uploadDataset,
  deleteDataset,
  getDatasetPreview,
  getDatasetStats,
  type Dataset,
  type DatasetStats,
  type DatasetPreviewResponse,
} from '@/api/datasets'

// ============== Router ==============

const router = useRouter()

// ============== State ==============

const loading = ref(false)
const uploading = ref(false)
const previewLoading = ref(false)
const statsLoading = ref(false)

const showUploadDialog = ref(false)
const showPreviewDialog = ref(false)
const showStatsDialog = ref(false)

const uploadFormRef = ref<FormInstance>()
const uploadRef = ref<UploadInstance>()

const filters = reactive({
  keyword: '',
  source: '',
  dateRange: null as [string, string] | null,
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

const uploadForm = reactive({
  name: '',
  source: 'custom',
  description: '',
  file: null as File | null,
})

const uploadRules = {
  name: [{ required: true, message: '请输入数据集名称', trigger: 'blur' }],
  source: [{ required: true, message: '请选择数据来源', trigger: 'change' }],
}

const datasets = ref<Dataset[]>([])
const previewDataset = ref<Dataset | null>(null)
const statsDataset = ref<Dataset | null>(null)
const currentStats = ref<DatasetStats | null>(null)

const previewData = reactive<DatasetPreviewResponse>({
  records: [],
  total: 0,
  page: 1,
  page_size: 50,
  pages: 0,
  columns: [],
})

const previewPagination = reactive({
  page: 1,
  pageSize: 50,
  total: 0,
})

// ============== Computed ==============

const totalStats = computed(() => ({
  datasets: pagination.total,
  drugs: datasets.value.reduce((sum, d) => sum + d.drug_count, 0),
  diseases: datasets.value.reduce((sum, d) => sum + d.disease_count, 0),
  associations: datasets.value.reduce((sum, d) => sum + d.association_count, 0),
}))

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

const getSourceTagType = (source: string) => {
  switch (source.toLowerCase()) {
    case 'drugbank':
      return 'success'
    case 'ctd':
      return 'warning'
    default:
      return 'info'
  }
}

const loadDatasets = async () => {
  loading.value = true
  try {
    const response = await listDatasets(pagination.page, pagination.pageSize, {
      keyword: filters.keyword || undefined,
      source: filters.source || undefined,
      start_date: filters.dateRange?.[0] || undefined,
      end_date: filters.dateRange?.[1] || undefined,
    })
    
    datasets.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    console.error('Failed to load datasets:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadDatasets()
}

const handleReset = () => {
  filters.keyword = ''
  filters.source = ''
  filters.dateRange = null
  handleSearch()
}

const handleSizeChange = () => {
  pagination.page = 1
  loadDatasets()
}

const handlePageChange = () => {
  loadDatasets()
}

const handleFileChange = (uploadFile: UploadFile) => {
  if (uploadFile.raw) {
    uploadForm.file = uploadFile.raw
  }
}

const handleFileRemove = () => {
  uploadForm.file = null
}

const handleUpload = async () => {
  if (!uploadFormRef.value) return
  
  const valid = await uploadFormRef.value.validate().catch(() => false)
  if (!valid) return
  
  if (!uploadForm.file) {
    ElMessage.warning('请选择要上传的文件')
    return
  }
  
  uploading.value = true
  try {
    await uploadDataset(
      uploadForm.file,
      uploadForm.name,
      uploadForm.source,
      uploadForm.description || undefined
    )
    
    ElMessage.success('上传成功')
    showUploadDialog.value = false
    
    // Reset form
    uploadForm.name = ''
    uploadForm.source = 'custom'
    uploadForm.description = ''
    uploadForm.file = null
    uploadRef.value?.clearFiles()
    
    // Reload datasets
    loadDatasets()
  } catch (error) {
    console.error('Upload failed:', error)
  } finally {
    uploading.value = false
  }
}

const handlePreview = async (row: Dataset) => {
  previewDataset.value = row
  previewPagination.page = 1
  showPreviewDialog.value = true
  await loadPreviewData(row.id)
}

const loadPreviewData = async (datasetId: number) => {
  previewLoading.value = true
  try {
    const response = await getDatasetPreview(
      datasetId,
      previewPagination.page,
      previewPagination.pageSize
    )
    
    previewData.records = response.data.records
    previewPagination.total = response.data.total
  } catch (error) {
    console.error('Failed to load preview:', error)
  } finally {
    previewLoading.value = false
  }
}

const handlePreviewSizeChange = () => {
  previewPagination.page = 1
  if (previewDataset.value) {
    loadPreviewData(previewDataset.value.id)
  }
}

const handlePreviewPageChange = () => {
  if (previewDataset.value) {
    loadPreviewData(previewDataset.value.id)
  }
}

const handleStats = async (row: Dataset) => {
  statsDataset.value = row
  showStatsDialog.value = true
  statsLoading.value = true
  
  try {
    const response = await getDatasetStats(row.id)
    currentStats.value = response.data
  } catch (error) {
    console.error('Failed to load stats:', error)
  } finally {
    statsLoading.value = false
  }
}

const handleBuildGraph = (row: Dataset) => {
  // Navigate to graph building page with dataset pre-selected
  router.push({
    path: '/graphs',
    query: { dataset_id: row.id.toString(), dataset_name: row.name }
  })
}

const handleDelete = async (row: Dataset) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除数据集 "${row.name}" 吗？此操作不可恢复。`,
      '确认删除',
      { type: 'warning' }
    )
    
    await deleteDataset(row.id)
    ElMessage.success('删除成功')
    loadDatasets()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Delete failed:', error)
    }
  }
}

// ============== Lifecycle ==============

onMounted(() => {
  loadDatasets()
})
</script>

<style lang="scss" scoped>
.dataset-list {
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
  .dataset-name {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .el-icon {
      color: var(--primary-light);
    }
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

:deep(.el-upload-dragger) {
  background: rgba(255, 255, 255, 0.02);
  border-color: var(--card-border);
  
  &:hover {
    border-color: var(--primary-light);
  }
}

.preview-pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.stats-dialog-content {
  min-height: 200px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.stats-item {
  text-align: center;
  padding: 20px;
  background: var(--card-bg);
  border-radius: 8px;
  border: 1px solid var(--card-border);
  
  .stats-item-label {
    font-size: 14px;
    color: var(--text-secondary);
    margin-bottom: 8px;
  }
  
  .stats-item-value {
    font-size: 24px;
    font-weight: 600;
    color: var(--text-primary);
    
    &.positive {
      color: var(--el-color-success);
    }
    
    &.negative {
      color: var(--el-color-info);
    }
  }
}
</style>
