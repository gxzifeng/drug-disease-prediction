import request from './index'
import { ResponseModel } from './index'
import { Experiment, ExperimentDetail, ExperimentComparison } from './experiments'

/**
 * 获取模型列表（已完成的实验）
 */
export function listModels(page = 1, pageSize = 10, params: any = {}) {
  return request.get<ResponseModel<any>>('/models', {
    params: {
      page,
      page_size: pageSize,
      ...params
    }
  })
}

/**
 * 获取激活模型
 */
export function getActiveModel() {
  return request.get<ResponseModel<Experiment>>('/models/active')
}

/**
 * 获取模型详情
 */
export function getModelDetail(modelId: number) {
  return request.get<ResponseModel<ExperimentDetail>>(`/models/${modelId}`)
}

/**
 * 激活模型
 */
export function activateModel(modelId: number) {
  return request.post<ResponseModel<Experiment>>(`/models/${modelId}/activate`)
}

/**
 * 删除模型
 */
export function deleteModel(modelId: number) {
  return request.delete<ResponseModel<any>>(`/models/${modelId}`)
}

/**
 * 对比模型
 */
export function compareModels(modelIds: number[]) {
  return request.post<ResponseModel<ExperimentComparison>>('/models/compare', modelIds)
}
