# 数据集管理 API

## 概述

数据集管理模块提供药物-疾病关联数据的上传、预览、统计和筛选功能。

## 数据格式

### CSV/TSV 文件格式

上传的文件应包含以下列：

| 列名 | 必需 | 描述 |
|------|------|------|
| drug_id | ✓ | 药物标识符 |
| drug_name | | 药物名称 |
| disease_id | ✓ | 疾病标识符 |
| disease_name | | 疾病名称 |
| label | | 关联标签 (0/1，默认为1) |

列名支持以下别名（不区分大小写）：
- drug_id: `drugid`, `drug`
- disease_id: `diseaseid`, `disease`
- drug_name: `drugname`
- disease_name: `diseasename`
- label: `association`, `relation`

## API 接口

### 1. 上传数据集

**POST** `/api/v1/datasets`

上传新的数据集文件。

#### 请求参数 (multipart/form-data)

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| file | File | ✓ | CSV/TSV 文件 |
| name | string | ✓ | 数据集名称 (1-200字符) |
| source | string | | 数据来源 (默认: "custom") |
| description | string | | 数据集描述 |

#### 响应示例

```json
{
  "code": 200,
  "message": "Dataset uploaded successfully",
  "data": {
    "id": 1,
    "name": "DrugBank-Disease Dataset",
    "description": "Drug-disease associations from DrugBank",
    "source": "drugbank",
    "original_filename": "drugbank_diseases.csv",
    "file_size": 102400,
    "drug_count": 1500,
    "disease_count": 800,
    "association_count": 5000,
    "positive_count": 4500,
    "negative_count": 500,
    "is_parsed": true,
    "parse_error": null,
    "created_by": 1,
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
  }
}
```

---

### 2. 获取数据集列表

**GET** `/api/v1/datasets`

获取数据集列表，支持分页和筛选。

#### 查询参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| page | int | 1 | 页码 (≥1) |
| page_size | int | 10 | 每页数量 (1-100) |
| keyword | string | | 搜索关键词 (名称/描述) |
| source | string | | 数据来源筛选 |
| start_date | datetime | | 开始日期 |
| end_date | datetime | | 结束日期 |

#### 响应示例

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "items": [
      {
        "id": 1,
        "name": "DrugBank-Disease Dataset",
        "description": "...",
        "source": "drugbank",
        "drug_count": 1500,
        "disease_count": 800,
        "association_count": 5000,
        "...": "..."
      }
    ],
    "total": 10,
    "page": 1,
    "page_size": 10,
    "pages": 1
  }
}
```

---

### 3. 获取数据集详情

**GET** `/api/v1/datasets/{dataset_id}`

获取单个数据集的详细信息。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| dataset_id | int | 数据集 ID |

#### 响应示例

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "id": 1,
    "name": "DrugBank-Disease Dataset",
    "description": "Drug-disease associations from DrugBank",
    "source": "drugbank",
    "original_filename": "drugbank_diseases.csv",
    "file_size": 102400,
    "drug_count": 1500,
    "disease_count": 800,
    "association_count": 5000,
    "positive_count": 4500,
    "negative_count": 500,
    "is_parsed": true,
    "parse_error": null,
    "created_by": 1,
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
  }
}
```

---

### 4. 数据集预览

**GET** `/api/v1/datasets/{dataset_id}/preview`

分页获取数据集记录预览。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| dataset_id | int | 数据集 ID |

#### 查询参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| page_size | int | 50 | 每页数量 (1-500) |

#### 响应示例

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "records": [
      {
        "id": 1,
        "drug_id": "DB00001",
        "drug_name": "Aspirin",
        "disease_id": "DOID:123",
        "disease_name": "Coronary Artery Disease",
        "label": 1
      }
    ],
    "total": 5000,
    "page": 1,
    "page_size": 50,
    "pages": 100,
    "columns": ["drug_id", "drug_name", "disease_id", "disease_name", "label"]
  }
}
```

---

### 5. 数据集统计

**GET** `/api/v1/datasets/{dataset_id}/stats`

获取数据集的统计信息。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| dataset_id | int | 数据集 ID |

#### 响应示例

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "drug_count": 1500,
    "disease_count": 800,
    "association_count": 5000,
    "positive_count": 4500,
    "negative_count": 500,
    "positive_ratio": 0.9
  }
}
```

---

### 6. 更新数据集

**PUT** `/api/v1/datasets/{dataset_id}`

更新数据集元信息（需要认证）。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| dataset_id | int | 数据集 ID |

#### 请求体

```json
{
  "name": "Updated Dataset Name",
  "description": "Updated description",
  "source": "custom"
}
```

所有字段均为可选，只更新提供的字段。

#### 响应

返回更新后的数据集详情。

---

### 7. 删除数据集

**DELETE** `/api/v1/datasets/{dataset_id}`

删除数据集及其关联文件（需要认证）。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| dataset_id | int | 数据集 ID |

#### 响应示例

```json
{
  "code": 200,
  "message": "Dataset deleted successfully",
  "data": null
}
```

---

## 错误码

| 状态码 | 说明 |
|--------|------|
| 400 | 请求参数错误 (如文件格式不支持) |
| 401 | 未认证 (需要登录的接口) |
| 404 | 数据集不存在 |
| 422 | 数据验证失败 |
| 500 | 服务器内部错误 |

## 验收标准

- [x] 能上传 CSV/TSV 文件并自动解析
- [x] 支持列名大小写不敏感匹配
- [x] 支持分页预览数据集内容
- [x] 支持按关键词、来源、时间筛选
- [x] 统计信息包含药物数、疾病数、关联数、正负样本比例
- [x] 删除数据集同时删除关联文件
