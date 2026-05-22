import axios from './index';
import type { ResponseModel } from './index';

// ======== Basic Prediction ========

export interface PredictionRequest {
  drug_id: string;
  disease_id: string;
  model_id?: number;
}

export interface PredictionResponse {
  drug_id: string;
  disease_id: string;
  drug_name?: string;
  disease_name?: string;
  probability: number;
  label: number;
  model_id: number;
  model_name: string;
}

export interface BatchPredictionRequest {
  dataset_id?: number;
  model_id?: number;
}

export interface BatchPredictionResponse {
  task_id: string;
  message: string;
}

export interface TaskStatusResponse {
  task_id: string;
  status: string;
  progress: number;
  message?: string;
  result?: any;
}

// ======== Recommendation ========

export interface DrugRecommendationRequest {
  disease_id: string;
  top_k?: number;
  model_id?: number;
}

export interface DrugRecommendationItem {
  drug_id: string;
  probability: number;
  label?: number;
  drug_name?: string;
}

export interface DrugRecommendationResponse {
  disease_id: string;
  disease_name?: string;
  model_id: number;
  model_name: string;
  items: DrugRecommendationItem[];
}

export interface DiseaseRecommendationRequest {
  drug_id: string;
  top_k?: number;
  model_id?: number;
}

export interface DiseaseRecommendationItem {
  disease_id: string;
  probability: number;
  label?: number;
  disease_name?: string;
}

export interface DiseaseRecommendationResponse {
  drug_id: string;
  drug_name?: string;
  model_id: number;
  model_name: string;
  items: DiseaseRecommendationItem[];
}

// ======== History ========

export interface PredictionHistoryItem {
  id: number;
  type: string;
  experiment_id?: number | null;
  user_id?: number | null;
  task_id?: string | null;
  status: string;
  error_message?: string | null;
  input_data: Record<string, any>;
  result?: any;
  created_at: string;
  completed_at?: string | null;
}

export interface PredictionHistoryResponse {
  items: PredictionHistoryItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface PredictionHistoryQuery {
  page?: number;
  page_size?: number;
  type?: string;
  experiment_id?: number;
}

const predictionsApi = {
  // 单例预测
  predictSingle: (data: PredictionRequest) => {
    return axios.post<ResponseModel<PredictionResponse>>('/predictions/predict', data);
  },
  
  // 批量预测
  predictBatch: (data: BatchPredictionRequest) => {
    return axios.post<ResponseModel<BatchPredictionResponse>>('/predictions/batch', data);
  },
  
  // 任务状态
  getTaskStatus: (taskId: string) => {
    return axios.get<ResponseModel<TaskStatusResponse>>(`/predictions/tasks/${taskId}`);
  },
  
  // 下载批量结果
  getDownloadUrl: (filename: string) => {
    return `${import.meta.env.VITE_API_BASE_URL || ''}/api/v1/predictions/download/${filename}`;
  },

  // 疾病 → 药物 推荐
  recommendDrugs: (data: DrugRecommendationRequest) => {
    return axios.post<ResponseModel<DrugRecommendationResponse>>(
      '/predictions/drug-recommendation',
      data,
    );
  },

  // 药物 → 疾病 推荐
  recommendDiseases: (data: DiseaseRecommendationRequest) => {
    return axios.post<ResponseModel<DiseaseRecommendationResponse>>(
      '/predictions/disease-recommendation',
      data,
    );
  },

  // 预测历史
  getHistory: (query: PredictionHistoryQuery) => {
    return axios.get<ResponseModel<PredictionHistoryResponse>>('/predictions/history', {
      params: {
        page: query.page,
        page_size: query.page_size,
        type: query.type || undefined,
        experiment_id: query.experiment_id,
      },
    });
  },
};

export default predictionsApi;
