# 模型管理 API

## 概述

对训练完成的模型（实验结果）进行管理，包括列表查看、激活、删除等。

## API 接口

### 1. 获取模型列表

**GET** `/api/v1/models`

获取所有训练成功的分类模型。

#### 响应示例

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "items": [
      {
        "id": 1,
        "name": "RF_Node2Vec_Exp_1",
        "algorithm": "random_forest",
        "embedding_method": "node2vec",
        "feature_method": "hadamard",
        "metrics": {
          "auc_roc": 0.92,
          "auc_pr": 0.89,
          "f1": 0.85
        },
        "is_active": true,
        "created_at": "2024-01-20T12:00:00"
      }
    ],
    "total": 5
  }
}
```

---

### 2. 设置激活模型

**POST** `/api/v1/models/{model_id}/activate`

将指定模型设为系统默认预测模型。

---

### 3. 删除模型

**DELETE** `/api/v1/models/{model_id}`

删除模型记录及其对应的磁盘文件。

---

### 4. 获取特征重要性

**GET** `/api/v1/models/{model_id}/feature-importance`

获取模型的特征重要性排序（如果支持，如随机森林、XGBoost）。

#### 响应示例

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "features": ["dim_10", "dim_120", "dim_45", "..."],
    "importance": [0.15, 0.12, 0.08, "..."]
  }
}
```
