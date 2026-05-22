import api, { ApiResponse } from './index'
import { SubgraphResponse } from './graphs'

// ============== Types ==============

export interface RandomForestParams {
  n_estimators?: number
  max_depth?: number | null
  min_samples_split?: number
  min_samples_leaf?: number
  class_weight?: string | null
}

export interface XGBoostParams {
  n_estimators?: number
  max_depth?: number
  learning_rate?: number
  subsample?: number
  colsample_bytree?: number
  scale_pos_weight?: number | null
}

export interface SVMParams {
  C?: number
  kernel?: 'linear' | 'rbf' | 'poly' | 'sigmoid'
  gamma?: string
  probability?: boolean
  class_weight?: string | null
}

export interface Experiment {
  id: number
  name: string
  description: string | null
  embedding_id: number
  classifier: 'random_forest' | 'xgboost' | 'svm'
  feature_method: 'concat' | 'hadamard' | 'l1' | 'l2' | 'average'
  random_seed: number
  test_size: number
  k_fold: number | null
  classifier_params: Record<string, any> | null
  accuracy: number | null
  precision: number | null
  recall: number | null
  f1_score: number | null
  auc_roc: number | null
  auc_pr: number | null
  kfold_metrics: KFoldMetrics | null
  feature_importance: { importances: number[] } | null
  confusion_matrix: ConfusionMatrix | null
  training_time_seconds: number | null
  num_train_samples: number | null
  num_test_samples: number | null
  num_features: number | null
  model_path: string | null
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  error_message: string | null
  task_id: string | null
  is_active: boolean
  created_by: number | null
  created_at: string
  updated_at: string
  started_at: string | null
  completed_at: string | null
}

export interface MetricsResponse {
  accuracy: number | null
  precision: number | null
  recall: number | null
  f1_score: number | null
  auc_roc: number | null
  auc_pr: number | null
}

export interface KFoldMetrics {
  fold_metrics: MetricsResponse[]
  mean_metrics: MetricsResponse
  std_metrics: MetricsResponse
}

export interface ConfusionMatrix {
  tn: number
  fp: number
  fn: number
  tp: number
}

export interface FeatureImportanceItem {
  feature_name: string
  importance: number
}

export interface ExperimentDetail extends Omit<Experiment, 'feature_importance'> {
  embedding_name: string
  graph_id: number
  graph_name: string
  metrics: MetricsResponse | null
  feature_importance: FeatureImportanceItem[] | null
}

export interface ExperimentListResponse {
  items: Experiment[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface ExperimentTrainRequest {
  embedding_id: number
  name: string
  description?: string
  classifier: 'random_forest' | 'xgboost' | 'svm'
  feature_method?: 'concat' | 'hadamard' | 'l1' | 'l2' | 'average'
  random_seed?: number
  test_size?: number
  k_fold?: number
  random_forest_params?: RandomForestParams
  xgboost_params?: XGBoostParams
  svm_params?: SVMParams
}

export interface ExperimentUpdateRequest {
  name?: string
  description?: string
}

export interface ExperimentFilter {
  keyword?: string
  embedding_id?: number
  classifier?: 'random_forest' | 'xgboost' | 'svm'
  status?: 'pending' | 'running' | 'completed' | 'failed'
}

export interface ExperimentComparison {
  experiments: Experiment[]
  best_by_auc_roc: number | null
  best_by_f1: number | null
}

// ============== API Functions ==============

/**
 * Create and start training an experiment
 */
export async function trainExperiment(request: ExperimentTrainRequest): Promise<ApiResponse<Experiment>> {
  return api.post('/experiments/train', request)
}

/**
 * Create an experiment without starting training
 */
export async function createExperiment(request: ExperimentTrainRequest): Promise<ApiResponse<Experiment>> {
  return api.post('/experiments', request)
}

/**
 * Start training for an existing experiment
 */
export async function startExperimentTraining(id: number): Promise<ApiResponse<Experiment>> {
  return api.post(`/experiments/${id}/start`)
}

/**
 * List experiments with filtering and pagination
 */
export async function listExperiments(
  page: number = 1,
  pageSize: number = 10,
  filters?: ExperimentFilter
): Promise<ApiResponse<ExperimentListResponse>> {
  const params: Record<string, string | number> = {
    page,
    page_size: pageSize,
  }

  if (filters?.keyword) {
    params.keyword = filters.keyword
  }
  if (filters?.embedding_id !== undefined) {
    params.embedding_id = filters.embedding_id
  }
  if (filters?.classifier) {
    params.classifier = filters.classifier
  }
  if (filters?.status) {
    params.status = filters.status
  }

  return api.get('/experiments', { params })
}

/**
 * Get experiment by ID
 */
export async function getExperiment(id: number): Promise<ApiResponse<Experiment>> {
  return api.get(`/experiments/${id}`)
}

/**
 * Get detailed experiment information
 */
export async function getExperimentDetail(id: number): Promise<ApiResponse<ExperimentDetail>> {
  return api.get(`/experiments/${id}/detail`)
}

/**
 * Update experiment metadata
 */
export async function updateExperiment(
  id: number,
  data: ExperimentUpdateRequest
): Promise<ApiResponse<Experiment>> {
  return api.put(`/experiments/${id}`, data)
}

/**
 * Delete an experiment
 */
export async function deleteExperiment(id: number): Promise<ApiResponse<null>> {
  return api.delete(`/experiments/${id}`)
}

/**
 * Set an experiment as the active model
 */
export async function activateExperiment(id: number): Promise<ApiResponse<Experiment>> {
  return api.post(`/experiments/${id}/activate`)
}

/**
 * Get the currently active model
 */
export async function getActiveModel(): Promise<ApiResponse<Experiment | null>> {
  return api.get('/experiments/active')
}

/**
 * Compare multiple experiments
 */
export async function compareExperiments(ids: number[]): Promise<ApiResponse<ExperimentComparison>> {
  return api.post('/experiments/compare', ids)
}

/**
 * Get all experiments for a specific embedding
 */
export async function getExperimentsByEmbedding(embeddingId: number): Promise<ApiResponse<Experiment[]>> {
  return api.get(`/experiments/embedding/${embeddingId}`)
}

/**
 * Get top predicted associations as a subgraph
 */
export async function getTopPredictions(
  id: number,
  limit: number = 50
): Promise<ApiResponse<SubgraphResponse>> {
  return api.get(`/experiments/${id}/top-predictions`, { params: { limit } })
}

// Default export
export default {
  trainExperiment,
  createExperiment,
  startExperimentTraining,
  listExperiments,
  getExperiment,
  getExperimentDetail,
  updateExperiment,
  deleteExperiment,
  activateExperiment,
  getActiveModel,
  compareExperiments,
  getExperimentsByEmbedding,
  getTopPredictions,
}
