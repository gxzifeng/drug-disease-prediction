import api, { ApiResponse } from './index'

// ============== Types ==============

export interface Node2VecParams {
  walk_length?: number
  num_walks?: number
  p?: number
  q?: number
  window_size?: number
}

export interface GCNParams {
  hidden_channels?: number
  num_layers?: number
  dropout?: number
}

export interface Embedding {
  id: number
  name: string
  description: string | null
  graph_id: number
  algorithm: 'node2vec' | 'gcn'
  embedding_dim: number
  epochs: number
  learning_rate: number
  random_seed: number
  node2vec_params: Node2VecParams | null
  gcn_params: GCNParams | null
  training_loss: number | null
  val_loss: number | null
  training_time_seconds: number | null
  training_history: TrainingHistoryData | null
  embedding_path: string | null
  model_path: string | null
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  error_message: string | null
  task_id: string | null
  created_by: number | null
  created_at: string
  updated_at: string
  started_at: string | null
  completed_at: string | null
}

export interface EmbeddingDetail extends Embedding {
  graph_name: string
  num_nodes: number
  num_edges: number
  training_history: TrainingHistory | null
}

export interface TrainingHistoryData {
  epochs: number[]
  train_losses: number[]
  val_losses?: number[]
}

export interface TrainingHistory {
  epochs: number[]
  train_losses: number[]
  val_losses: number[] | null
}

export interface TrainingProgress {
  status: string
  progress: number
  current_epoch: number | null
  current_loss: number | null
  current_val_loss: number | null
}

export interface EmbeddingListResponse {
  items: Embedding[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface EmbeddingTrainRequest {
  graph_id: number
  name: string
  description?: string
  algorithm: 'node2vec' | 'gcn'
  embedding_dim?: number
  epochs?: number
  learning_rate?: number
  random_seed?: number
  node2vec_params?: Node2VecParams
  gcn_params?: GCNParams
}

export interface EmbeddingUpdateRequest {
  name?: string
  description?: string
}

export interface EmbeddingFilter {
  keyword?: string
  graph_id?: number
  algorithm?: 'node2vec' | 'gcn'
  status?: 'pending' | 'running' | 'completed' | 'failed'
}

// ============== API Functions ==============

/** 训练接口可能耗时较长，单独延长超时时间（10 分钟） */
const TRAIN_TIMEOUT_MS = 10 * 60 * 1000

/**
 * Create and start training an embedding
 */
export async function trainEmbedding(request: EmbeddingTrainRequest): Promise<ApiResponse<Embedding>> {
  return api.post('/embeddings/train', request, { timeout: TRAIN_TIMEOUT_MS })
}

/**
 * Create an embedding without starting training
 */
export async function createEmbedding(request: EmbeddingTrainRequest): Promise<ApiResponse<Embedding>> {
  return api.post('/embeddings', request)
}

/**
 * Start training for an existing embedding
 */
export async function startTraining(id: number): Promise<ApiResponse<Embedding>> {
  return api.post(`/embeddings/${id}/start`, undefined, { timeout: TRAIN_TIMEOUT_MS })
}

/**
 * List embeddings with filtering and pagination
 */
export async function listEmbeddings(
  page: number = 1,
  pageSize: number = 10,
  filters?: EmbeddingFilter
): Promise<ApiResponse<EmbeddingListResponse>> {
  const params: Record<string, string | number> = {
    page,
    page_size: pageSize,
  }

  if (filters?.keyword) {
    params.keyword = filters.keyword
  }
  if (filters?.graph_id !== undefined) {
    params.graph_id = filters.graph_id
  }
  if (filters?.algorithm) {
    params.algorithm = filters.algorithm
  }
  if (filters?.status) {
    params.status = filters.status
  }

  return api.get('/embeddings', { params })
}

/**
 * Get embedding by ID
 */
export async function getEmbedding(id: number): Promise<ApiResponse<Embedding>> {
  return api.get(`/embeddings/${id}`)
}

/**
 * Get detailed embedding information
 */
export async function getEmbeddingDetail(id: number): Promise<ApiResponse<EmbeddingDetail>> {
  return api.get(`/embeddings/${id}/detail`)
}

/**
 * Get training progress
 */
export async function getTrainingProgress(id: number): Promise<ApiResponse<TrainingProgress>> {
  return api.get(`/embeddings/${id}/progress`)
}

/**
 * Get training history with loss curves
 */
export async function getTrainingHistory(id: number): Promise<ApiResponse<TrainingHistory>> {
  return api.get(`/embeddings/${id}/history`)
}

/**
 * Update embedding metadata
 */
export async function updateEmbedding(
  id: number,
  data: EmbeddingUpdateRequest
): Promise<ApiResponse<Embedding>> {
  return api.put(`/embeddings/${id}`, data)
}

/**
 * Delete an embedding
 */
export async function deleteEmbedding(id: number): Promise<ApiResponse<null>> {
  return api.delete(`/embeddings/${id}`)
}

/**
 * Get all embeddings for a specific graph
 */
export async function getEmbeddingsByGraph(graphId: number): Promise<ApiResponse<Embedding[]>> {
  return api.get(`/embeddings/graph/${graphId}`)
}

// Default export
export default {
  trainEmbedding,
  createEmbedding,
  startTraining,
  listEmbeddings,
  getEmbedding,
  getEmbeddingDetail,
  getTrainingProgress,
  getTrainingHistory,
  updateEmbedding,
  deleteEmbedding,
  getEmbeddingsByGraph,
}
