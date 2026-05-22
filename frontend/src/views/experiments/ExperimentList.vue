<template>
  <div class="experiment-list fade-in">
    <div class="page-header">
      <h1>分类器实验</h1>
      <p>训练机器学习分类器预测药物-疾病关联</p>
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
          v-model="filters.classifier"
          placeholder="分类器类型"
          clearable
          style="width: 150px"
          @change="fetchExperiments"
        >
          <el-option label="Random Forest" value="random_forest" />
          <el-option label="XGBoost" value="xgboost" />
          <el-option label="SVM" value="svm" />
        </el-select>
        <el-select
          v-model="filters.status"
          placeholder="状态"
          clearable
          style="width: 120px"
          @change="fetchExperiments"
        >
          <el-option label="待训练" value="pending" />
          <el-option label="训练中" value="running" />
          <el-option label="已完成" value="completed" />
          <el-option label="失败" value="failed" />
        </el-select>
      </div>
      <el-button type="primary" :icon="Plus" @click="showTrainDialog">
        新建实验
      </el-button>
    </div>

    <!-- Experiment List -->
    <el-table
      v-loading="loading"
      :data="experiments"
      stripe
      style="width: 100%"
      @row-click="handleRowClick"
    >
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="名称" min-width="150">
        <template #default="{ row }">
          <div class="name-cell">
            <el-link type="primary" :underline="false">{{ row.name }}</el-link>
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
      <el-table-column prop="feature_method" label="特征方法" width="100">
        <template #default="{ row }">
          {{ getFeatureMethodName(row.feature_method) }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="small">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="评估指标" width="280">
        <template #default="{ row }">
          <div v-if="row.status === 'completed'" class="metrics-cell">
            <el-tooltip content="AUC-ROC">
              <span class="metric">
                <strong>AUC:</strong> {{ formatMetric(row.auc_roc) }}
              </span>
            </el-tooltip>
            <el-tooltip content="F1 Score">
              <span class="metric">
                <strong>F1:</strong> {{ formatMetric(row.f1_score) }}
              </span>
            </el-tooltip>
            <el-tooltip content="Accuracy">
              <span class="metric">
                <strong>Acc:</strong> {{ formatMetric(row.accuracy) }}
              </span>
            </el-tooltip>
          </div>
          <span v-else class="no-metrics">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="training_time_seconds" label="训练时间" width="100">
        <template #default="{ row }">
          {{ row.training_time_seconds ? `${row.training_time_seconds.toFixed(2)}s` : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="160">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
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
            v-if="row.status === 'completed' && !row.is_active"
            type="success"
            link
            size="small"
            @click.stop="handleActivate(row)"
          >
            激活
          </el-button>
          <el-button
            type="danger"
            link
            size="small"
            :disabled="row.status === 'running'"
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
        @size-change="fetchExperiments"
        @current-change="fetchExperiments"
      />
    </div>

    <!-- Train Dialog -->
    <el-dialog
      v-model="trainDialogVisible"
      title="新建分类器实验"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form ref="trainFormRef" :model="trainForm" :rules="trainRules" label-width="120px">
        <el-form-item label="实验名称" prop="name">
          <el-input v-model="trainForm.name" placeholder="请输入实验名称" />
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input v-model="trainForm.description" type="textarea" :rows="2" placeholder="可选描述" />
        </el-form-item>
        
        <el-form-item label="选择嵌入" prop="embedding_id">
          <el-select v-model="trainForm.embedding_id" placeholder="选择已训练的嵌入" style="width: 100%">
            <el-option
              v-for="emb in availableEmbeddings"
              :key="emb.id"
              :label="`${emb.name} (${emb.algorithm}, ${emb.embedding_dim}维)`"
              :value="emb.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="分类器类型" prop="classifier">
          <el-radio-group v-model="trainForm.classifier">
            <el-radio-button value="random_forest">Random Forest</el-radio-button>
            <el-radio-button value="xgboost">XGBoost</el-radio-button>
            <el-radio-button value="svm">SVM</el-radio-button>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="特征组合方法" prop="feature_method">
          <el-select v-model="trainForm.feature_method" style="width: 200px">
            <el-option label="Concat (拼接)" value="concat" />
            <el-option label="Hadamard (点乘)" value="hadamard" />
            <el-option label="L1 (绝对差)" value="l1" />
            <el-option label="L2 (平方差)" value="l2" />
            <el-option label="Average (平均)" value="average" />
          </el-select>
        </el-form-item>
        
        <el-divider content-position="left">训练设置</el-divider>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="测试集比例">
              <el-input-number v-model="trainForm.test_size" :min="0.1" :max="0.5" :step="0.05" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="随机种子">
              <el-input-number v-model="trainForm.random_seed" :min="0" :max="99999" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="K折交叉验证">
              <el-input-number v-model="trainForm.k_fold" :min="0" :max="10" placeholder="0表示不使用" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <!-- Random Forest Parameters -->
        <template v-if="trainForm.classifier === 'random_forest'">
          <el-divider content-position="left">Random Forest 参数</el-divider>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="树数量">
                <el-input-number v-model="trainForm.random_forest_params.n_estimators" :min="10" :max="1000" :step="10" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="最大深度">
                <el-input-number v-model="trainForm.random_forest_params.max_depth" :min="1" :max="50" placeholder="空为不限制" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="最小分裂样本">
                <el-input-number v-model="trainForm.random_forest_params.min_samples_split" :min="2" :max="20" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="最小叶子样本">
                <el-input-number v-model="trainForm.random_forest_params.min_samples_leaf" :min="1" :max="20" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
        </template>
        
        <!-- XGBoost Parameters -->
        <template v-if="trainForm.classifier === 'xgboost'">
          <el-divider content-position="left">XGBoost 参数</el-divider>
          
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="迭代次数">
                <el-input-number v-model="trainForm.xgboost_params.n_estimators" :min="10" :max="1000" :step="10" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="最大深度">
                <el-input-number v-model="trainForm.xgboost_params.max_depth" :min="1" :max="20" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="学习率">
                <el-input-number v-model="trainForm.xgboost_params.learning_rate" :min="0.01" :max="1" :step="0.01" :precision="2" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="样本采样比例">
                <el-input-number v-model="trainForm.xgboost_params.subsample" :min="0.5" :max="1" :step="0.1" :precision="1" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="特征采样比例">
                <el-input-number v-model="trainForm.xgboost_params.colsample_bytree" :min="0.5" :max="1" :step="0.1" :precision="1" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
        </template>
        
        <!-- SVM Parameters -->
        <template v-if="trainForm.classifier === 'svm'">
          <el-divider content-position="left">SVM 参数</el-divider>
          
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="正则化参数C">
                <el-input-number v-model="trainForm.svm_params.C" :min="0.01" :max="100" :step="0.1" :precision="2" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="核函数">
                <el-select v-model="trainForm.svm_params.kernel" style="width: 100%">
                  <el-option label="RBF" value="rbf" />
                  <el-option label="Linear" value="linear" />
                  <el-option label="Polynomial" value="poly" />
                  <el-option label="Sigmoid" value="sigmoid" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="Gamma">
                <el-select v-model="trainForm.svm_params.gamma" style="width: 100%">
                  <el-option label="Scale" value="scale" />
                  <el-option label="Auto" value="auto" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </template>
      </el-form>
      
      <template #footer>
        <el-button @click="trainDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleTrain">
          开始训练
        </el-button>
      </template>
    </el-dialog>

    <!-- Detail Dialog -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="selectedExperiment?.name || '实验详情'"
      width="1000px"
    >
      <template v-if="experimentDetail">
        <el-tabs v-model="activeTab">
          <!-- Basic Info Tab -->
          <el-tab-pane label="基本信息" name="info">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="ID">{{ experimentDetail.id }}</el-descriptions-item>
              <el-descriptions-item label="名称">{{ experimentDetail.name }}</el-descriptions-item>
              <el-descriptions-item label="分类器">
                <el-tag :type="getClassifierType(experimentDetail.classifier)">
                  {{ getClassifierName(experimentDetail.classifier) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="getStatusType(experimentDetail.status)">
                  {{ getStatusText(experimentDetail.status) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="嵌入">{{ experimentDetail.embedding_name }}</el-descriptions-item>
              <el-descriptions-item label="图">{{ experimentDetail.graph_name }}</el-descriptions-item>
              <el-descriptions-item label="特征方法">{{ getFeatureMethodName(experimentDetail.feature_method) }}</el-descriptions-item>
              <el-descriptions-item label="测试集比例">{{ experimentDetail.test_size }}</el-descriptions-item>
              <el-descriptions-item label="K折验证">{{ experimentDetail.k_fold || '未启用' }}</el-descriptions-item>
              <el-descriptions-item label="随机种子">{{ experimentDetail.random_seed }}</el-descriptions-item>
              <el-descriptions-item label="训练样本数">{{ experimentDetail.num_train_samples || '-' }}</el-descriptions-item>
              <el-descriptions-item label="测试样本数">{{ experimentDetail.num_test_samples || '-' }}</el-descriptions-item>
              <el-descriptions-item label="特征维度">{{ experimentDetail.num_features || '-' }}</el-descriptions-item>
              <el-descriptions-item label="训练时间">
                {{ experimentDetail.training_time_seconds ? `${experimentDetail.training_time_seconds.toFixed(2)}s` : '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">
                {{ formatDate(experimentDetail.created_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="是否激活">
                <el-tag :type="experimentDetail.is_active ? 'success' : 'info'" size="small">
                  {{ experimentDetail.is_active ? '是' : '否' }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
            
            <!-- Classifier Parameters -->
            <div v-if="experimentDetail.classifier_params" class="params-section">
              <h4>分类器参数</h4>
              <el-descriptions :column="3" border size="small">
                <el-descriptions-item 
                  v-for="(value, key) in experimentDetail.classifier_params" 
                  :key="key" 
                  :label="key"
                >
                  {{ value ?? '空' }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
            
            <div v-if="experimentDetail.status === 'failed'" class="error-section">
              <el-alert type="error" :title="selectedExperiment?.error_message || '训练失败'" :closable="false" show-icon />
            </div>
          </el-tab-pane>
          
          <!-- Metrics Tab -->
          <el-tab-pane label="评估指标" name="metrics">
            <div v-if="experimentDetail.metrics" class="metrics-section">
              <el-row :gutter="20">
                <el-col :span="8">
                  <el-card class="metric-card">
                    <template #header>
                      <div class="metric-header">
                        <span>AUC-ROC</span>
                        <el-tooltip content="Area Under ROC Curve, 越接近1越好">
                          <el-icon><InfoFilled /></el-icon>
                        </el-tooltip>
                      </div>
                    </template>
                    <div class="metric-value">{{ formatMetric(experimentDetail.metrics.auc_roc) }}</div>
                  </el-card>
                </el-col>
                <el-col :span="8">
                  <el-card class="metric-card">
                    <template #header>
                      <div class="metric-header">
                        <span>AUC-PR</span>
                        <el-tooltip content="Area Under Precision-Recall Curve">
                          <el-icon><InfoFilled /></el-icon>
                        </el-tooltip>
                      </div>
                    </template>
                    <div class="metric-value">{{ formatMetric(experimentDetail.metrics.auc_pr) }}</div>
                  </el-card>
                </el-col>
                <el-col :span="8">
                  <el-card class="metric-card">
                    <template #header>
                      <div class="metric-header">
                        <span>F1 Score</span>
                        <el-tooltip content="Precision和Recall的调和平均">
                          <el-icon><InfoFilled /></el-icon>
                        </el-tooltip>
                      </div>
                    </template>
                    <div class="metric-value">{{ formatMetric(experimentDetail.metrics.f1_score) }}</div>
                  </el-card>
                </el-col>
              </el-row>
              
              <el-row :gutter="20" style="margin-top: 20px">
                <el-col :span="8">
                  <el-card class="metric-card">
                    <template #header>Accuracy</template>
                    <div class="metric-value">{{ formatMetric(experimentDetail.metrics.accuracy) }}</div>
                  </el-card>
                </el-col>
                <el-col :span="8">
                  <el-card class="metric-card">
                    <template #header>Precision</template>
                    <div class="metric-value">{{ formatMetric(experimentDetail.metrics.precision) }}</div>
                  </el-card>
                </el-col>
                <el-col :span="8">
                  <el-card class="metric-card">
                    <template #header>Recall</template>
                    <div class="metric-value">{{ formatMetric(experimentDetail.metrics.recall) }}</div>
                  </el-card>
                </el-col>
              </el-row>
              
              <!-- Confusion Matrix -->
              <div v-if="experimentDetail.confusion_matrix" class="confusion-section">
                <h4>混淆矩阵</h4>
                <div class="confusion-matrix">
                  <table>
                    <thead>
                      <tr>
                        <th></th>
                        <th>预测负</th>
                        <th>预测正</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td><strong>实际负</strong></td>
                        <td class="tn">{{ experimentDetail.confusion_matrix.tn }}</td>
                        <td class="fp">{{ experimentDetail.confusion_matrix.fp }}</td>
                      </tr>
                      <tr>
                        <td><strong>实际正</strong></td>
                        <td class="fn">{{ experimentDetail.confusion_matrix.fn }}</td>
                        <td class="tp">{{ experimentDetail.confusion_matrix.tp }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
              
              <!-- K-Fold Metrics -->
              <div v-if="experimentDetail.kfold_metrics" class="kfold-section">
                <h4>K折交叉验证结果</h4>
                <el-descriptions :column="3" border size="small">
                  <el-descriptions-item label="平均 AUC-ROC">
                    {{ formatMetric(experimentDetail.kfold_metrics.mean_metrics.auc_roc) }}
                    ± {{ formatMetric(experimentDetail.kfold_metrics.std_metrics.auc_roc) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="平均 F1">
                    {{ formatMetric(experimentDetail.kfold_metrics.mean_metrics.f1_score) }}
                    ± {{ formatMetric(experimentDetail.kfold_metrics.std_metrics.f1_score) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="平均 Accuracy">
                    {{ formatMetric(experimentDetail.kfold_metrics.mean_metrics.accuracy) }}
                    ± {{ formatMetric(experimentDetail.kfold_metrics.std_metrics.accuracy) }}
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </div>
            <el-empty v-else description="暂无评估指标" />
          </el-tab-pane>
          
          <!-- Feature Importance Tab -->
          <el-tab-pane label="特征重要性" name="importance">
            <div v-if="experimentDetail.feature_importance && experimentDetail.feature_importance.length > 0" class="chart-container">
              <v-chart :option="featureImportanceOption" autoresize style="height: 500px" />
            </div>
            <el-empty v-else description="暂无特征重要性数据" />
          </el-tab-pane>

          <!-- Top Predictions Tab -->
          <el-tab-pane label="预测 TopK" name="predictions">
            <el-table
              v-if="topPredictions && topPredictions.length > 0"
              :data="topPredictions"
              stripe
              style="width: 100%"
              height="400"
            >
              <el-table-column type="index" label="#" width="50" />
              <el-table-column prop="source" label="药物 ID" />
              <el-table-column prop="target" label="疾病 ID" />
              <el-table-column prop="weight" label="预测概率">
                <template #default="{ row }">
                  <el-progress
                    :percentage="Math.round(row.weight * 100)"
                    :color="getProbabilityColor(row.weight)"
                  />
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-else description="暂无预测数据" />
          </el-tab-pane>
        </el-tabs>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus'
import { Plus, Search, InfoFilled } from '@element-plus/icons-vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import dayjs from 'dayjs'

import {
  listExperiments,
  trainExperiment,
  getExperimentDetail,
  deleteExperiment,
  activateExperiment,
  getTopPredictions,
  Experiment,
  ExperimentDetail,
  ExperimentFilter,
  ExperimentTrainRequest,
} from '@/api/experiments'
import { listEmbeddings, Embedding } from '@/api/embeddings'
import { GraphEdge } from '@/api/graphs'

// Register ECharts components
use([
  CanvasRenderer,
  BarChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
])

// State
const loading = ref(false)
const submitting = ref(false)
const experiments = ref<Experiment[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const filters = reactive<ExperimentFilter>({
  keyword: '',
  classifier: undefined,
  status: undefined,
})

// Dialog state
const trainDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const trainFormRef = ref<FormInstance>()
const selectedExperiment = ref<Experiment | null>(null)
const experimentDetail = ref<ExperimentDetail | null>(null)
const topPredictions = ref<GraphEdge[]>([])
const activeTab = ref('info')
const availableEmbeddings = ref<Embedding[]>([])

// Train form
type TrainFormType = ExperimentTrainRequest & {
  random_forest_params: Required<NonNullable<ExperimentTrainRequest['random_forest_params']>>
  xgboost_params: Required<NonNullable<ExperimentTrainRequest['xgboost_params']>>
  svm_params: Required<NonNullable<ExperimentTrainRequest['svm_params']>>
}

const defaultTrainForm = (): TrainFormType => ({
  embedding_id: 0,
  name: '',
  description: '',
  classifier: 'random_forest',
  feature_method: 'concat',
  random_seed: 42,
  test_size: 0.2,
  k_fold: 0,
  random_forest_params: {
    n_estimators: 100,
    max_depth: null,
    min_samples_split: 2,
    min_samples_leaf: 1,
    class_weight: 'balanced',
  },
  xgboost_params: {
    n_estimators: 100,
    max_depth: 6,
    learning_rate: 0.1,
    subsample: 0.8,
    colsample_bytree: 0.8,
    scale_pos_weight: null,
  },
  svm_params: {
    C: 1.0,
    kernel: 'rbf',
    gamma: 'scale',
    probability: true,
    class_weight: 'balanced',
  },
})

const trainForm = reactive(defaultTrainForm())

const trainRules = {
  name: [{ required: true, message: '请输入实验名称', trigger: 'blur' }],
  embedding_id: [{ required: true, message: '请选择嵌入', trigger: 'change' }],
  classifier: [{ required: true, message: '请选择分类器', trigger: 'change' }],
}

// Computed
const featureImportanceOption = computed(() => {
  if (!experimentDetail.value?.feature_importance) {
    return {}
  }

  const data = experimentDetail.value.feature_importance
  const names = data.map(d => d.feature_name)
  const values = data.map(d => d.importance)

  return {
    title: {
      text: 'Top 20 特征重要性',
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    grid: {
      left: '15%',
      right: '5%',
      bottom: '3%',
      top: '50px',
      containLabel: true,
    },
    xAxis: {
      type: 'value',
      name: '重要性',
    },
    yAxis: {
      type: 'category',
      data: names.reverse(),
      axisLabel: {
        interval: 0,
      },
    },
    series: [
      {
        name: '重要性',
        type: 'bar',
        data: values.reverse(),
        itemStyle: {
          color: '#409EFF',
        },
      },
    ],
  }
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
    fetchExperiments()
  }, 300)
}

const fetchExperiments = async () => {
  loading.value = true
  try {
    const response = await listExperiments(currentPage.value, pageSize.value, {
      keyword: filters.keyword || undefined,
      classifier: filters.classifier || undefined,
      status: filters.status || undefined,
    })
    experiments.value = response.data.items
    total.value = response.data.total
  } catch (error) {
    console.error('Failed to fetch experiments:', error)
  } finally {
    loading.value = false
  }
}

const fetchEmbeddings = async () => {
  try {
    const response = await listEmbeddings(1, 100, { status: 'completed' })
    availableEmbeddings.value = response.data.items
  } catch (error) {
    console.error('Failed to fetch embeddings:', error)
  }
}

const showTrainDialog = async () => {
  await fetchEmbeddings()
  if (availableEmbeddings.value.length === 0) {
    ElMessage.warning('请先完成嵌入训练再进行分类器实验')
    return
  }
  Object.assign(trainForm, defaultTrainForm())
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
    const request: ExperimentTrainRequest = {
      embedding_id: trainForm.embedding_id,
      name: trainForm.name,
      description: trainForm.description || undefined,
      classifier: trainForm.classifier,
      feature_method: trainForm.feature_method,
      random_seed: trainForm.random_seed,
      test_size: trainForm.test_size,
      k_fold: trainForm.k_fold && trainForm.k_fold >= 2 ? trainForm.k_fold : undefined,
    }

    if (trainForm.classifier === 'random_forest') {
      request.random_forest_params = { ...trainForm.random_forest_params }
    } else if (trainForm.classifier === 'xgboost') {
      request.xgboost_params = { ...trainForm.xgboost_params }
    } else if (trainForm.classifier === 'svm') {
      request.svm_params = { ...trainForm.svm_params }
    }

    await trainExperiment(request)
    ElMessage.success('实验已创建并开始训练')
    trainDialogVisible.value = false
    fetchExperiments()
  } catch (error) {
    console.error('Failed to create experiment:', error)
  } finally {
    submitting.value = false
  }
}

const handleRowClick = (row: Experiment) => {
  viewDetail(row)
}

const viewDetail = async (experiment: Experiment) => {
  selectedExperiment.value = experiment
  activeTab.value = 'info'
  detailDialogVisible.value = true
  topPredictions.value = []

  try {
    const response = await getExperimentDetail(experiment.id)
    experimentDetail.value = response.data
    
    // Also fetch top predictions for the predictions tab
    if (experiment.status === 'completed') {
      const predRes = await getTopPredictions(experiment.id, 50)
      topPredictions.value = predRes.data.edges
    }
  } catch (error) {
    console.error('Failed to fetch experiment detail:', error)
    experimentDetail.value = null
  }
}

const getProbabilityColor = (prob: number) => {
  if (prob > 0.8) return '#67C23A'
  if (prob > 0.5) return '#E6A23C'
  return '#F56C6C'
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

    await activateExperiment(experiment.id)
    ElMessage.success('模型已激活')
    fetchExperiments()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to activate experiment:', error)
    }
  }
}

const handleDelete = async (experiment: Experiment) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除实验 "${experiment.name}" 吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await deleteExperiment(experiment.id)
    ElMessage.success('删除成功')
    fetchExperiments()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete experiment:', error)
    }
  }
}

// Lifecycle
onMounted(() => {
  fetchExperiments()
})
</script>

<style lang="scss" scoped>
.experiment-list {
  max-width: 1600px;
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

.name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.metrics-cell {
  display: flex;
  gap: 12px;
  font-size: 12px;
  
  .metric {
    white-space: nowrap;
    
    strong {
      color: var(--text-secondary);
    }
  }
}

.no-metrics {
  color: var(--text-secondary);
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

.metrics-section {
  .metric-card {
    text-align: center;
    
    .metric-header {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }
    
    .metric-value {
      font-size: 32px;
      font-weight: 600;
      color: var(--el-color-primary);
    }
  }
}

.confusion-section {
  margin-top: 24px;
  
  h4 {
    margin-bottom: 12px;
    color: var(--text-primary);
    font-weight: 500;
  }
  
  .confusion-matrix {
    display: flex;
    justify-content: center;
    
    table {
      border-collapse: collapse;
      text-align: center;
      
      th, td {
        padding: 12px 24px;
        border: 1px solid var(--el-border-color);
      }
      
      th {
        background: var(--el-fill-color-light);
        font-weight: 500;
      }
      
      .tn, .tp {
        background: var(--el-color-success-light-9);
        color: var(--el-color-success);
        font-weight: 600;
      }
      
      .fp, .fn {
        background: var(--el-color-danger-light-9);
        color: var(--el-color-danger);
        font-weight: 600;
      }
    }
  }
}

.kfold-section {
  margin-top: 24px;
  
  h4 {
    margin-bottom: 12px;
    color: var(--text-primary);
    font-weight: 500;
  }
}

.chart-container {
  padding: 20px 0;
}

:deep(.el-descriptions__label) {
  width: 120px;
}
</style>
