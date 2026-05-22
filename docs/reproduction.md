# 实验复现指南

本指南详细说明了如何复现药物-疾病关联预测系统的完整实验流程，确保结果可验证和可重复。

## 目录

1. [环境准备](#环境准备)
2. [数据准备](#数据准备)
3. [实验流程](#实验流程)
4. [参数配置](#参数配置)
5. [结果验证](#结果验证)
6. [常见问题](#常见问题)

## 环境准备

### 系统要求

- **操作系统**: Windows 10+, Linux, macOS
- **Python**: 3.10+
- **Node.js**: 18+
- **内存**: 8GB+ (GCN 训练建议 16GB+)
- **存储**: 10GB+ 可用空间

### 1. 克隆项目

```bash
    cd d:\cursor\backend
cd drug-disease-prediction
```

### 2. 后端环境

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 启动服务

#### 使用 Docker Compose（推荐）

```bash
docker-compose up -d
```

#### 手动启动

```bash
# 启动 MySQL 和 Redis（需预先安装）
# 然后启动后端
cd backend
uvicorn app.main:app --reload --port 8000

# 启动 Celery Worker
celery -A app.core.celery_app worker --loglevel=info

# 启动前端
cd frontend
npm install
npm run dev
```

### 4. 数据库迁移

```bash
cd backend
alembic upgrade head
```

## 数据准备

### 数据格式要求

CSV 文件需包含以下列：

| 列名 | 必填 | 说明 |
|------|------|------|
| drug_id | ✓ | 药物唯一标识符 |
| disease_id | ✓ | 疾病唯一标识符 |
| drug_name | | 药物名称（可选） |
| disease_name | | 疾病名称（可选） |
| label | | 关联标签，0或1（默认1） |

### 示例数据

使用项目提供的示例数据：

```
data/sample_drug_disease.csv
```

或准备自己的数据文件：

```csv
drug_id,disease_id,drug_name,disease_name,label
DB00001,MESH:D003920,Metformin,Diabetes Mellitus,1
DB00002,MESH:D006973,Aspirin,Hypertension,1
...
```

### 上传数据集

1. 登录系统（默认管理员账号：admin/admin123）
2. 导航至"数据集管理"页面
3. 点击"上传数据集"按钮
4. 选择 CSV 文件并填写名称和来源
5. 确认上传

**API 方式：**

```bash
curl -X POST "http://localhost:8000/api/v1/datasets" \
  -H "Authorization: Bearer <token>" \
  -F "name=MyDataset" \
  -F "source=custom" \
  -F "file=@data/sample_drug_disease.csv"
```

## 实验流程

### 完整实验链路

```
数据集 → 图构建 → 嵌入学习 → 分类训练 → 模型预测
```

### 步骤 1：构建图网络

**参数说明：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| train_ratio | 0.8 | 训练集比例 |
| val_ratio | 0.1 | 验证集比例 |
| test_ratio | 0.1 | 测试集比例 |
| negative_ratio | 1.0 | 负采样比例 |
| random_seed | 42 | 随机种子 |

**操作步骤：**

1. 进入"图网络构建"页面
2. 选择目标数据集
3. 配置划分比例（建议保持默认 8:1:1）
4. 设置负采样比例（1.0 表示正负样本 1:1）
5. 设置随机种子（默认 42，确保可复现）
6. 点击"开始构建"

**API 方式：**

```bash
curl -X POST "http://localhost:8000/api/v1/graphs/build" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": 1,
    "name": "MyGraph",
    "train_ratio": 0.8,
    "val_ratio": 0.1,
    "test_ratio": 0.1,
    "negative_ratio": 1.0,
    "random_seed": 42
  }'
```

### 步骤 2：特征学习（Embedding）

#### Node2Vec 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| dimension | 128 | 嵌入维度 |
| walk_length | 80 | 随机游走长度 |
| num_walks | 10 | 每节点游走次数 |
| p | 1.0 | 返回参数 |
| q | 1.0 | 进出参数 |
| window_size | 5 | Skip-gram 窗口大小 |
| epochs | 5 | 训练轮数 |

**操作步骤：**

1. 进入"模型训练"页面
2. 选择"特征学习"
3. 选择已构建的图
4. 选择算法（Node2Vec）
5. 配置参数
6. 点击"开始训练"

**API 方式：**

```bash
curl -X POST "http://localhost:8000/api/v1/embeddings/train" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "graph_id": 1,
    "name": "MyEmbedding",
    "method": "node2vec",
    "dimension": 128,
    "params": {
      "walk_length": 80,
      "num_walks": 10,
      "p": 1.0,
      "q": 1.0,
      "window_size": 5,
      "epochs": 5
    },
    "random_seed": 42
  }'
```

### 步骤 3：分类模型训练

#### 分类器选项

| 分类器 | 说明 |
|--------|------|
| random_forest | 随机森林（推荐） |
| xgboost | XGBoost 梯度提升 |
| svm | 支持向量机 |

#### 特征融合方法

| 方法 | 说明 |
|------|------|
| hadamard | 逐元素乘积（推荐） |
| concat | 向量拼接 |
| l1 | L1 距离 |
| l2 | L2 距离 |
| average | 平均值 |

**操作步骤：**

1. 选择"分类模型训练"
2. 选择已完成的 Embedding
3. 选择分类器（推荐 Random Forest）
4. 选择特征融合方法（推荐 Hadamard）
5. 配置分类器参数
6. 点击"开始实验"

**API 方式：**

```bash
curl -X POST "http://localhost:8000/api/v1/experiments/train" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "embedding_id": 1,
    "name": "MyExperiment",
    "classifier": "random_forest",
    "feature_method": "hadamard",
    "params": {
      "n_estimators": 100,
      "max_depth": 10,
      "random_state": 42
    }
  }'
```

### 步骤 4：模型预测

#### 单例预测

```bash
curl -X POST "http://localhost:8000/api/v1/predictions/predict" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "drug_id": "DB00001",
    "disease_id": "MESH:D003920",
    "model_id": 1
  }'
```

#### 批量预测

```bash
curl -X POST "http://localhost:8000/api/v1/predictions/batch" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": 2,
    "model_id": 1
  }'
```

## 参数配置

### 推荐实验配置

#### 配置 1：快速验证

适用于快速验证流程是否正确：

```json
{
  "graph": {
    "train_ratio": 0.8,
    "negative_ratio": 0.5,
    "random_seed": 42
  },
  "embedding": {
    "method": "node2vec",
    "dimension": 64,
    "walk_length": 40,
    "num_walks": 5,
    "epochs": 3
  },
  "classifier": {
    "type": "random_forest",
    "n_estimators": 50,
    "feature_method": "hadamard"
  }
}
```

#### 配置 2：标准实验

适用于论文复现和基准测试：

```json
{
  "graph": {
    "train_ratio": 0.8,
    "negative_ratio": 1.0,
    "random_seed": 42
  },
  "embedding": {
    "method": "node2vec",
    "dimension": 128,
    "walk_length": 80,
    "num_walks": 10,
    "epochs": 5
  },
  "classifier": {
    "type": "random_forest",
    "n_estimators": 100,
    "feature_method": "hadamard"
  }
}
```

#### 配置 3：高精度

适用于追求最佳性能：

```json
{
  "graph": {
    "train_ratio": 0.8,
    "negative_ratio": 1.0,
    "random_seed": 42
  },
  "embedding": {
    "method": "node2vec",
    "dimension": 256,
    "walk_length": 100,
    "num_walks": 20,
    "epochs": 10
  },
  "classifier": {
    "type": "xgboost",
    "n_estimators": 200,
    "max_depth": 8,
    "feature_method": "hadamard"
  }
}
```

## 结果验证

### 评估指标

| 指标 | 说明 | 期望范围 |
|------|------|----------|
| AUC-ROC | ROC 曲线下面积 | 0.80-0.95 |
| AUC-PR | PR 曲线下面积 | 0.75-0.90 |
| F1 Score | F1 分数 | 0.70-0.85 |
| Accuracy | 准确率 | 0.80-0.90 |
| Precision | 精确率 | 0.75-0.90 |
| Recall | 召回率 | 0.75-0.90 |

### 复现验证清单

- [ ] 使用相同的随机种子（42）
- [ ] 使用相同的数据集
- [ ] 使用相同的划分比例
- [ ] 使用相同的算法参数
- [ ] 验证 AUC-ROC 差异 < 0.01
- [ ] 验证 F1 Score 差异 < 0.02

### 导出实验结果

```bash
# 获取实验详情
curl "http://localhost:8000/api/v1/experiments/1/detail" \
  -H "Authorization: Bearer <token>"

# 比较多个实验
curl -X POST "http://localhost:8000/api/v1/experiments/compare" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '[1, 2, 3]'
```

## 常见问题

### Q1: 嵌入训练很慢

**解决方案：**
- 减少 `num_walks` 和 `walk_length` 参数
- 减小 `dimension` 维度
- 使用更小的数据集进行测试

### Q2: 内存不足

**解决方案：**
- 减少负采样比例
- 使用更小的嵌入维度
- 分批处理大数据集

### Q3: 预测结果不稳定

**解决方案：**
- 确保设置了随机种子
- 增加训练轮数
- 增大训练集比例

### Q4: 模型评估指标较低

**可能原因：**
- 数据质量问题
- 参数未调优
- 负样本比例过高

**解决方案：**
- 检查数据中是否有噪声
- 尝试不同的特征融合方法
- 调整分类器参数

### Q5: 任务长时间处于 Running 状态

**解决方案：**
- 检查 Celery Worker 是否正常运行
- 检查 Redis 连接是否正常
- 查看 Worker 日志排查错误

## 联系支持

如有问题，请通过以下方式联系：

- GitHub Issues
- Email: support@example.com
