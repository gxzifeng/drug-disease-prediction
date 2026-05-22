import api, { ApiResponse } from './index'

// ============== Types ==============

export interface Graph {
  id: number
  name: string
  description: string | null
  dataset_id: number
  negative_sample_ratio: number
  train_ratio: number
  val_ratio: number
  test_ratio: number
  random_seed: number
  num_drug_nodes: number
  num_disease_nodes: number
  num_total_nodes: number
  num_edges: number
  num_positive_edges: number
  num_negative_edges: number
  num_train_edges: number
  num_val_edges: number
  num_test_edges: number
  is_built: boolean
  build_error: string | null
  created_by: number | null
  created_at: string
  updated_at: string
}

export interface GraphSummary {
  id: number
  name: string
  dataset_id: number
  dataset_name: string
  num_drug_nodes: number
  num_disease_nodes: number
  num_total_nodes: number
  num_edges: number
  num_positive_edges: number
  num_negative_edges: number
  positive_ratio: number
  num_train_edges: number
  num_val_edges: number
  num_test_edges: number
  train_ratio_actual: number
  val_ratio_actual: number
  test_ratio_actual: number
  negative_sample_ratio: number
  random_seed: number
  is_built: boolean
  created_at: string
}

export interface GraphListResponse {
  items: Graph[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface GraphBuildRequest {
  dataset_id: number
  name: string
  description?: string
  negative_sample_ratio?: number
  train_ratio?: number
  val_ratio?: number
  test_ratio?: number
  random_seed?: number
}

export interface GraphUpdateRequest {
  name?: string
  description?: string
}

export interface GraphFilter {
  keyword?: string
  dataset_id?: number
  is_built?: boolean
}

export interface NodeIndexMapping {
  drug_to_idx: Record<string, number>
  disease_to_idx: Record<string, number>
  idx_to_drug: Record<number, string>
  idx_to_disease: Record<number, string>
}

export interface GraphNode {
  id: string
  name: string
  type: 'drug' | 'disease'
}

export interface GraphEdge {
  source: string
  target: string
  label: number
  type: 'original' | 'predicted'
  weight?: number
}

export interface SubgraphResponse {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

// ============== API Functions ==============

/**
 * Build a new graph from a dataset
 */
export async function buildGraph(request: GraphBuildRequest): Promise<ApiResponse<Graph>> {
  return api.post('/graphs/build', request)
}

/**
 * List graphs with filtering and pagination
 */
export async function listGraphs(
  page: number = 1,
  pageSize: number = 10,
  filters?: GraphFilter
): Promise<ApiResponse<GraphListResponse>> {
  const params: Record<string, string | number | boolean> = {
    page,
    page_size: pageSize,
  }

  if (filters?.keyword) {
    params.keyword = filters.keyword
  }
  if (filters?.dataset_id !== undefined) {
    params.dataset_id = filters.dataset_id
  }
  if (filters?.is_built !== undefined) {
    params.is_built = filters.is_built
  }

  return api.get('/graphs', { params })
}

/**
 * Get graph by ID
 */
export async function getGraph(id: number): Promise<ApiResponse<Graph>> {
  return api.get(`/graphs/${id}`)
}

/**
 * Get graph summary with detailed statistics
 */
export async function getGraphSummary(id: number): Promise<ApiResponse<GraphSummary>> {
  return api.get(`/graphs/${id}/summary`)
}

/**
 * Get node index mapping for a graph
 */
export async function getNodeIndex(id: number): Promise<ApiResponse<NodeIndexMapping>> {
  return api.get(`/graphs/${id}/node-index`)
}

/**
 * Update graph metadata
 */
export async function updateGraph(
  id: number,
  data: GraphUpdateRequest
): Promise<ApiResponse<Graph>> {
  return api.put(`/graphs/${id}`, data)
}

/**
 * Delete a graph
 */
export async function deleteGraph(id: number): Promise<ApiResponse<null>> {
  return api.delete(`/graphs/${id}`)
}

/**
 * Get all graphs built from a specific dataset
 */
export async function getGraphsByDataset(datasetId: number): Promise<ApiResponse<Graph[]>> {
  return api.get(`/graphs/dataset/${datasetId}`)
}

/**
 * Get a subgraph for visualization
 */
export async function getSubgraph(
  id: number,
  limit: number = 100,
  nodeId?: string
): Promise<ApiResponse<SubgraphResponse>> {
  const params: Record<string, string | number> = { limit }
  if (nodeId) {
    params.node_id = nodeId
  }
  return api.get(`/graphs/${id}/subgraph`, { params })
}

// Default export
export default {
  buildGraph,
  listGraphs,
  getGraph,
  getGraphSummary,
  getNodeIndex,
  updateGraph,
  deleteGraph,
  getGraphsByDataset,
  getSubgraph,
}
