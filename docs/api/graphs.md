# 图构建模块 API 文档

## 概述

图构建模块用于从数据集构建药物-疾病二部图，支持负采样、数据划分等功能。

## 接口列表

### POST /api/v1/graphs/build

构建一个新的二部图。

**请求体 (JSON):**

```json
{
  "dataset_id": 1,
  "name": "DrugBank_Graph_v1",
  "description": "基于 DrugBank 数据的关联网络",
  "negative_sample_ratio": 1.0,
  "train_ratio": 0.7,
  "val_ratio": 0.15,
  "test_ratio": 0.15,
  "random_seed": 42
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| dataset_id | int | 是 | 源数据集 ID |
| name | string | 是 | 图名称，1-200 字符 |
| description | string | 否 | 图描述 |
| negative_sample_ratio | float | 否 | 负采样比例，默认 1.0，范围 0.1-10.0 |
| train_ratio | float | 否 | 训练集比例，默认 0.7，范围 0.1-0.9 |
| val_ratio | float | 否 | 验证集比例，默认 0.15，范围 0.05-0.4 |
| test_ratio | float | 否 | 测试集比例，默认 0.15，范围 0.05-0.4 |
| random_seed | int | 否 | 随机种子，默认 42 |

> **注意：** train_ratio + val_ratio + test_ratio 必须等于 1.0

**响应示例:**

```json
{
  "code": 200,
  "message": "Graph built successfully",
  "data": {
    "id": 1,
    "name": "DrugBank_Graph_v1",
    "description": "基于 DrugBank 数据的关联网络",
    "dataset_id": 1,
    "negative_sample_ratio": 1.0,
    "train_ratio": 0.7,
    "val_ratio": 0.15,
    "test_ratio": 0.15,
    "random_seed": 42,
    "num_drug_nodes": 500,
    "num_disease_nodes": 300,
    "num_total_nodes": 800,
    "num_edges": 2000,
    "num_positive_edges": 1000,
    "num_negative_edges": 1000,
    "num_train_edges": 1400,
    "num_val_edges": 300,
    "num_test_edges": 300,
    "is_built": true,
    "build_error": null,
    "created_by": 1,
    "created_at": "2026-01-10T12:00:00Z",
    "updated_at": "2026-01-10T12:00:00Z"
  }
}
```

---

### GET /api/v1/graphs

获取图列表（分页）。

**查询参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页数量，默认 10，范围 1-100 |
| keyword | string | 否 | 搜索关键词（名称/描述） |
| dataset_id | int | 否 | 按数据集 ID 筛选 |
| is_built | bool | 否 | 按构建状态筛选 |

**响应示例:**

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "items": [...],
    "total": 50,
    "page": 1,
    "page_size": 10,
    "pages": 5
  }
}
```

---

### GET /api/v1/graphs/{graph_id}

获取图详情。

**响应:** 同 POST /graphs/build 的 data 结构。

---

### GET /api/v1/graphs/{graph_id}/summary

获取图的详细摘要统计信息。

**响应示例:**

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "id": 1,
    "name": "DrugBank_Graph_v1",
    "dataset_id": 1,
    "dataset_name": "DrugBank Dataset",
    "num_drug_nodes": 500,
    "num_disease_nodes": 300,
    "num_total_nodes": 800,
    "num_edges": 2000,
    "num_positive_edges": 1000,
    "num_negative_edges": 1000,
    "positive_ratio": 0.5,
    "num_train_edges": 1400,
    "num_val_edges": 300,
    "num_test_edges": 300,
    "train_ratio_actual": 0.7,
    "val_ratio_actual": 0.15,
    "test_ratio_actual": 0.15,
    "negative_sample_ratio": 1.0,
    "random_seed": 42,
    "is_built": true,
    "created_at": "2026-01-10T12:00:00Z"
  }
}
```

---

### GET /api/v1/graphs/{graph_id}/node-index

获取节点索引映射。

**响应示例:**

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "drug_to_idx": {
      "DB00001": 0,
      "DB00002": 1,
      ...
    },
    "disease_to_idx": {
      "DOID:0001": 500,
      "DOID:0002": 501,
      ...
    },
    "idx_to_drug": {
      "0": "DB00001",
      "1": "DB00002",
      ...
    },
    "idx_to_disease": {
      "500": "DOID:0001",
      "501": "DOID:0002",
      ...
    }
  }
}
```

---

### PUT /api/v1/graphs/{graph_id}

更新图元数据（需要登录）。

**请求体:**

```json
{
  "name": "Updated Graph Name",
  "description": "Updated description"
}
```

---

### DELETE /api/v1/graphs/{graph_id}

删除图及其关联文件（需要登录）。

---

### GET /api/v1/graphs/dataset/{dataset_id}

获取指定数据集的所有图。

**响应:** 图列表数组。

---

## 图产物文件

构建成功后，以下文件将保存在 `data/graphs/{graph_id}/` 目录：

| 文件 | 说明 |
|------|------|
| node_index.json | 节点索引映射（药物/疾病 ID 与索引的对应关系） |
| edge_index.npy | 边数据（numpy 数组，包含源节点、目标节点、标签） |
| train_edges.npy | 训练集边 |
| val_edges.npy | 验证集边 |
| test_edges.npy | 测试集边 |

---

## 错误码

| 状态码 | 说明 |
|--------|------|
| 400 | 参数错误（如比例之和不为 1、数据集未解析等） |
| 404 | 图或数据集不存在 |
| 500 | 服务器内部错误 |

---

## 验收标准

- [x] 能从数据集成功构建二部图
- [x] 支持自定义负采样比例
- [x] 支持自定义训练/验证/测试集划分
- [x] 支持设置随机种子以确保可复现
- [x] 图统计信息（节点数、边数、划分比例）与实际一致
- [x] 图产物可被后续训练任务引用
