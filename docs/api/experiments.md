# Experiments API 文档

## 概述

实验模块用于训练机器学习分类器（Random Forest、XGBoost、SVM）来预测药物-疾病关联。

## 接口列表

### 创建并训练实验

**POST** `/api/v1/experiments/train`

创建并立即开始训练一个分类器实验。

**请求体**:
```json
{
  "embedding_id": 1,
  "name": "RF实验-1",
  "description": "使用Random Forest进行预测",
  "classifier": "random_forest",
  "feature_method": "concat",
  "random_seed": 42,
  "test_size": 0.2,
  "k_fold": 5,
  "random_forest_params": {
    "n_estimators": 100,
    "max_depth": null,
    "min_samples_split": 2,
    "min_samples_leaf": 1,
    "class_weight": "balanced"
  }
}
```

**字段说明**:
- `embedding_id` (必填): 源嵌入ID
- `name` (必填): 实验名称
- `description` (可选): 实验描述
- `classifier` (必填): 分类器类型 (`random_forest`, `xgboost`, `svm`)
- `feature_method` (可选): 特征组合方法 (`concat`, `hadamard`, `l1`, `l2`, `average`)，默认 `concat`
- `random_seed` (可选): 随机种子，默认 42
- `test_size` (可选): 测试集比例，默认 0.2
- `k_fold` (可选): K折交叉验证，不设置则不启用
- `random_forest_params` (可选): RF参数
- `xgboost_params` (可选): XGBoost参数
- `svm_params` (可选): SVM参数

**响应**:
```json
{
  "code": 200,
  "message": "Experiment training started",
  "data": {
    "id": 1,
    "name": "RF实验-1",
    "classifier": "random_forest",
    "status": "completed",
    "auc_roc": 0.92,
    "f1_score": 0.85,
    ...
  }
}
```

### 列表查询

**GET** `/api/v1/experiments`

**查询参数**:
- `page`: 页码，默认 1
- `page_size`: 每页数量，默认 10
- `keyword`: 名称/描述搜索
- `embedding_id`: 按嵌入ID筛选
- `classifier`: 按分类器类型筛选
- `status`: 按状态筛选

### 获取详情

**GET** `/api/v1/experiments/{experiment_id}/detail`

返回详细的实验信息，包括评估指标、特征重要性、混淆矩阵等。

### 激活模型

**POST** `/api/v1/experiments/{experiment_id}/activate`

将指定实验设为激活模型，用于预测服务。

### 获取当前激活模型

**GET** `/api/v1/experiments/active`

### 删除实验

**DELETE** `/api/v1/experiments/{experiment_id}`

## 分类器参数

### Random Forest
- `n_estimators`: 树的数量 (10-1000)
- `max_depth`: 最大深度 (null表示不限制)
- `min_samples_split`: 分裂所需最小样本数
- `min_samples_leaf`: 叶节点最小样本数
- `class_weight`: 类别权重 ("balanced" 或 null)

### XGBoost
- `n_estimators`: 迭代次数 (10-1000)
- `max_depth`: 最大深度 (1-20)
- `learning_rate`: 学习率 (0.01-1.0)
- `subsample`: 样本采样比例 (0.5-1.0)
- `colsample_bytree`: 特征采样比例 (0.5-1.0)
- `scale_pos_weight`: 正样本权重

### SVM
- `C`: 正则化参数 (0.01-100)
- `kernel`: 核函数 ("linear", "rbf", "poly", "sigmoid")
- `gamma`: 核系数 ("scale", "auto")
- `probability`: 是否计算概率

## 特征组合方法

- **concat**: 拼接药物和疾病嵌入 `[drug_emb; disease_emb]`
- **hadamard**: 元素级乘法 `drug_emb * disease_emb`
- **l1**: 绝对差 `|drug_emb - disease_emb|`
- **l2**: 平方差 `(drug_emb - disease_emb)^2`
- **average**: 平均值 `(drug_emb + disease_emb) / 2`

## 评估指标

- **AUC-ROC**: ROC曲线下面积
- **AUC-PR**: 精确率-召回率曲线下面积
- **F1 Score**: 精确率和召回率的调和平均
- **Accuracy**: 准确率
- **Precision**: 精确率
- **Recall**: 召回率
- **Confusion Matrix**: 混淆矩阵 (TN, FP, FN, TP)
