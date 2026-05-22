import api, { ApiResponse } from './index'

// ============== Types ==============

export interface DatasetRecord {
  id: number
  drug_id: string
  drug_name: string | null
  disease_id: string
  disease_name: string | null
  label: number
}

export interface Dataset {
  id: number
  name: string
  description: string | null
  source: string
  original_filename: string
  file_size: number
  drug_count: number
  disease_count: number
  association_count: number
  positive_count: number
  negative_count: number
  is_parsed: boolean
  parse_error: string | null
  created_by: number | null
  created_at: string
  updated_at: string
}

export interface DatasetStats {
  drug_count: number
  disease_count: number
  association_count: number
  positive_count: number
  negative_count: number
  positive_ratio: number
}

export interface DatasetListResponse {
  items: Dataset[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface DatasetPreviewResponse {
  records: DatasetRecord[]
  total: number
  page: number
  page_size: number
  pages: number
  columns: string[]
}

export interface DatasetFilter {
  keyword?: string
  source?: string
  start_date?: string
  end_date?: string
}

export interface DatasetUpdateRequest {
  name?: string
  description?: string
  source?: string
}

// ============== API Functions ==============

/**
 * Upload a new dataset
 */
export async function uploadDataset(
  file: File,
  name: string,
  source: string = 'custom',
  description?: string
): Promise<ApiResponse<Dataset>> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('name', name)
  formData.append('source', source)
  if (description) {
    formData.append('description', description)
  }

  return api.post('/datasets', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}

/**
 * List datasets with filtering and pagination
 */
export async function listDatasets(
  page: number = 1,
  pageSize: number = 10,
  filters?: DatasetFilter
): Promise<ApiResponse<DatasetListResponse>> {
  const params: Record<string, string | number> = {
    page,
    page_size: pageSize,
  }

  if (filters?.keyword) {
    params.keyword = filters.keyword
  }
  if (filters?.source) {
    params.source = filters.source
  }
  if (filters?.start_date) {
    params.start_date = filters.start_date
  }
  if (filters?.end_date) {
    params.end_date = filters.end_date
  }

  return api.get('/datasets', { params })
}

/**
 * Get dataset by ID
 */
export async function getDataset(id: number): Promise<ApiResponse<Dataset>> {
  return api.get(`/datasets/${id}`)
}

/**
 * Get dataset preview (paginated records)
 */
export async function getDatasetPreview(
  id: number,
  page: number = 1,
  pageSize: number = 50
): Promise<ApiResponse<DatasetPreviewResponse>> {
  return api.get(`/datasets/${id}/preview`, {
    params: { page, page_size: pageSize },
  })
}

/**
 * Get dataset statistics
 */
export async function getDatasetStats(id: number): Promise<ApiResponse<DatasetStats>> {
  return api.get(`/datasets/${id}/stats`)
}

/**
 * Update dataset metadata
 */
export async function updateDataset(
  id: number,
  data: DatasetUpdateRequest
): Promise<ApiResponse<Dataset>> {
  return api.put(`/datasets/${id}`, data)
}

/**
 * Delete a dataset
 */
export async function deleteDataset(id: number): Promise<ApiResponse<null>> {
  return api.delete(`/datasets/${id}`)
}

// Default export
export default {
  uploadDataset,
  listDatasets,
  getDataset,
  getDatasetPreview,
  getDatasetStats,
  updateDataset,
  deleteDataset,
}
