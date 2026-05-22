# 预测服务 API

## 概述

提供基于已训练模型的药物-疾病关联预测功能，支持单例即时预测和批量异步预测。

## API 接口

### 1. 单例预测

**POST** `/api/v1/predictions/predict`

进行单个药物-疾病对的关联预测。

#### 请求体

```json
{
  "drug_id": "DB00001",
  "disease_id": "DOID:123",
  "model_id": 1
}
```

- `model_id` 为可选，若不提供则使用系统当前激活的模型。

#### 响应示例

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "drug_id": "DB00001",
    "disease_id": "DOID:123",
    "probability": 0.85,
    "label": 1,
    "model_id": 1,
    "model_name": "RF_Node2Vec_Exp_1"
  }
}
```

---

### 2. 批量预测任务创建

**POST** `/api/v1/predictions/batch`

创建一个批量预测任务（异步处理）。

#### 请求体

```json
{
  "dataset_id": 2,
  "model_id": 1
}
```

#### 响应示例

```json
{
  "code": 200,
  "message": "Batch prediction task started",
  "data": {
    "task_id": "b3e9a0f1-4c2d-4e8a-9a0b-1c2d3e4f5g6h"
  }
}
```

---

### 3. 查询任务状态

**GET** `/api/v1/predictions/tasks/{task_id}`

查询异步任务（预测或训练）的进度和状态。

#### 响应示例

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "task_id": "b3e9a0f1-...",
    "status": "SUCCESS",
    "progress": 100,
    "message": "Task completed successfully",
    "result": {
      "total_pairs": 1000,
      "predicted_pairs": 1000,
      "filename": "prediction_b3e9a0f1.csv",
      "download_url": "/api/v1/predictions/download/prediction_b3e9a0f1.csv",
      "completed_at": "2024-01-20T15:30:00"
    }
  }
}
```

---

### 4. 下载预测结果

**GET** `/api/v1/predictions/download/{filename}`

下载批量预测生成的 CSV 结果文件。

---

### 5. 获取 Top 预测关联（可视化）

**GET** `/api/v1/predictions/top-predictions/{model_id}`

获取模型预测出的置信度最高的关联，用于前端网络图展示。

#### 查询参数

- `limit`: 返回记录数，默认 50。

#### 响应示例

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "nodes": [
      {"id": "DB001", "name": "Drug A", "type": "drug"},
      {"id": "DOID:01", "name": "Disease X", "type": "disease"}
    ],
    "edges": [
      {"source": "DB001", "target": "DOID:01", "weight": 0.98, "type": "predicted"}
    ]
  }
}
```
