# Embeddings API 文档

## 概述

Embedding API 提供了训练和管理节点嵌入的功能，支持 Node2Vec 和 GCN 两种算法。

## 接口列表

### 1. 创建并开始训练

**POST** `/api/v1/embeddings/train`

创建嵌入训练任务并立即开始训练。

**请求体:**

```json
{
  "graph_id": 1,
  "name": "node2vec_exp1",
  "description": "Node2Vec 实验 1",
  "algorithm": "node2vec",
  "embedding_dim": 64,
  "epochs": 100,
  "learning_rate": 0.01,
  "random_seed": 42,
  "node2vec_params": {
    "walk_length": 80,
    "num_walks": 10,
    "p": 1.0,
    "q": 1.0,
    "window_size": 5
  }
}
```

**响应:**

```json
{
  "code": 200,
  "message": "Training started",
  "data": {
    "id": 1,
    "name": "node2vec_exp1",
    "algorithm": "node2vec",
    "status": "running",
    "progress": 0,
    ...
  }
}
```

### 2. 创建训练任务（不开始）

**POST** `/api/v1/embeddings`

仅创建训练任务，不立即开始训练。

### 3. 开始训练

**POST** `/api/v1/embeddings/{embedding_id}/start`

开始一个已创建的训练任务。

### 4. 获取训练列表

**GET** `/api/v1/embeddings`

**查询参数:**
- `page`: 页码（默认 1）
- `page_size`: 每页数量（默认 10，最大 100）
- `keyword`: 关键词搜索（名称/描述）
- `graph_id`: 按图 ID 筛选
- `algorithm`: 算法类型（node2vec/gcn）
- `status`: 状态（pending/running/completed/failed）

### 5. 获取训练详情

**GET** `/api/v1/embeddings/{embedding_id}`

### 6. 获取详细信息（含图信息和历史）

**GET** `/api/v1/embeddings/{embedding_id}/detail`

### 7. 获取训练进度

**GET** `/api/v1/embeddings/{embedding_id}/progress`

**响应:**

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "status": "running",
    "progress": 45,
    "current_epoch": 45,
    "current_loss": 0.3245,
    "current_val_loss": 0.4123
  }
}
```

### 8. 获取训练历史（损失曲线）

**GET** `/api/v1/embeddings/{embedding_id}/history`

**响应:**

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "epochs": [1, 2, 3, ...],
    "train_losses": [0.8, 0.6, 0.5, ...],
    "val_losses": [0.9, 0.7, 0.6, ...]
  }
}
```

### 9. 更新训练元数据

**PUT** `/api/v1/embeddings/{embedding_id}`

**请求体:**

```json
{
  "name": "新名称",
  "description": "新描述"
}
```

### 10. 删除训练

**DELETE** `/api/v1/embeddings/{embedding_id}`

### 11. 获取图的所有嵌入

**GET** `/api/v1/embeddings/graph/{graph_id}`

## 算法参数说明

### Node2Vec 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| walk_length | int | 80 | 随机游走长度 |
| num_walks | int | 10 | 每个节点的游走次数 |
| p | float | 1.0 | 返回参数，控制重访已访问节点的概率 |
| q | float | 1.0 | 进出参数，控制搜索行为（BFS vs DFS） |
| window_size | int | 5 | Skip-gram 上下文窗口大小 |

### GCN 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| hidden_channels | int | 64 | 隐藏层维度 |
| num_layers | int | 2 | GCN 层数 |
| dropout | float | 0.5 | Dropout 率 |

## 训练状态

- `pending`: 待训练
- `running`: 训练中
- `completed`: 已完成
- `failed`: 失败

## 错误码

- `400`: 请求参数错误（如图未构建、算法不支持等）
- `404`: 资源不存在
- `500`: 服务器内部错误
