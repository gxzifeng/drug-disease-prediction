# 测试指南

本文档介绍如何运行和编写药物-疾病关联预测系统的测试。

## 测试结构

```
backend/tests/
├── conftest.py          # 测试配置和通用 fixtures
├── api/
│   ├── test_auth.py     # 认证接口测试
│   ├── test_datasets.py # 数据集接口测试
│   ├── test_embeddings.py # 嵌入接口测试
│   ├── test_experiments.py # 实验接口测试
│   ├── test_graphs.py   # 图接口测试
│   ├── test_health.py   # 健康检查测试
│   ├── test_predictions.py # 预测接口测试
│   └── test_users.py    # 用户管理测试
├── test_boundary.py     # 边界条件测试
└── test_performance.py  # 性能基准测试
```

## 环境准备

### 1. 安装测试依赖

```bash
cd backend
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx aiosqlite
```

### 2. 配置测试环境

测试使用内存数据库（SQLite），无需额外配置数据库。

## 运行测试

### 运行所有测试

```bash
cd backend
pytest
```

### 运行特定模块测试

```bash
# 运行认证测试
pytest tests/api/test_auth.py

# 运行数据集测试
pytest tests/api/test_datasets.py

# 运行边界测试
pytest tests/test_boundary.py

# 运行性能测试
pytest tests/test_performance.py
```

### 运行特定测试类

```bash
pytest tests/api/test_auth.py::TestRegister
```

### 运行特定测试函数

```bash
pytest tests/api/test_auth.py::TestRegister::test_register_success
```

### 显示详细输出

```bash
pytest -v
```

### 显示打印输出

```bash
pytest -s
```

### 生成覆盖率报告

```bash
pip install pytest-cov
pytest --cov=app --cov-report=html
# 报告生成在 htmlcov/ 目录
```

## 测试类型

### 1. 单元测试

测试单个函数或类的功能：

```python
@pytest.mark.asyncio
async def test_password_hash():
    from app.core.security import get_password_hash, verify_password
    hashed = get_password_hash("testpassword")
    assert verify_password("testpassword", hashed)
    assert not verify_password("wrongpassword", hashed)
```

### 2. 集成测试

测试 API 端点的完整请求/响应流程：

```python
@pytest.mark.asyncio
async def test_create_dataset(client: AsyncClient, auth_headers: dict):
    csv_content = b"drug_id,disease_id,label\nD001,DIS001,1\n"
    files = {"file": ("data.csv", csv_content, "text/csv")}
    response = await client.post(
        "/api/v1/datasets",
        data={"name": "Test", "source": "test"},
        files=files,
        headers=auth_headers,
    )
    assert response.status_code == 200
```

### 3. 边界测试

测试边界条件和异常情况：

```python
@pytest.mark.asyncio
async def test_upload_empty_file(client: AsyncClient, auth_headers: dict):
    files = {"file": ("empty.csv", b"", "text/csv")}
    response = await client.post(
        "/api/v1/datasets",
        data={"name": "Empty", "source": "test"},
        files=files,
        headers=auth_headers,
    )
    assert response.status_code == 400
```

### 4. 性能测试

测试响应时间和并发处理能力：

```python
@pytest.mark.asyncio
async def test_health_check_response_time(client: AsyncClient):
    import time
    start = time.time()
    response = await client.get("/api/v1/health")
    elapsed = time.time() - start
    
    assert response.status_code == 200
    assert elapsed < 0.1  # 应在 100ms 内响应
```

## 测试 Fixtures

### 常用 Fixtures

| Fixture | 描述 |
|---------|------|
| `client` | 异步 HTTP 客户端 |
| `db_session` | 数据库会话 |
| `test_user` | 测试用户对象 |
| `auth_headers` | 带认证的请求头 |
| `admin_user` | 管理员用户对象 |
| `admin_headers` | 管理员请求头 |

### 自定义 Fixture 示例

```python
@pytest.fixture
async def test_dataset(db_session: AsyncSession) -> Dataset:
    """创建测试数据集"""
    dataset = Dataset(
        name="Test Dataset",
        source="test",
        original_filename="test.csv",
        file_path="/tmp/test.csv",
        file_size=1000,
        is_parsed=True,
    )
    db_session.add(dataset)
    await db_session.commit()
    await db_session.refresh(dataset)
    return dataset
```

## 编写测试的最佳实践

### 1. 测试命名

- 测试文件以 `test_` 开头
- 测试类以 `Test` 开头
- 测试函数以 `test_` 开头
- 名称应描述测试的内容

```python
# Good
class TestUserRegistration:
    async def test_register_with_valid_data_succeeds(self):
        ...
    
    async def test_register_with_duplicate_email_fails(self):
        ...

# Bad
class Tests:
    async def test1(self):
        ...
```

### 2. AAA 模式

每个测试应遵循 Arrange-Act-Assert 模式：

```python
async def test_create_dataset(client, auth_headers):
    # Arrange - 准备测试数据
    csv_content = b"drug_id,disease_id,label\nD001,DIS001,1\n"
    files = {"file": ("data.csv", csv_content, "text/csv")}
    
    # Act - 执行被测试的操作
    response = await client.post(
        "/api/v1/datasets",
        data={"name": "Test", "source": "test"},
        files=files,
        headers=auth_headers,
    )
    
    # Assert - 验证结果
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["name"] == "Test"
```

### 3. 测试独立性

- 每个测试应该独立运行
- 不依赖其他测试的执行顺序
- 使用 fixtures 提供测试数据

### 4. 测试覆盖

确保覆盖以下场景：
- 正常流程（Happy Path）
- 边界条件
- 错误处理
- 权限验证
- 输入验证

## 持续集成

### GitHub Actions 配置示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov httpx aiosqlite
      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 故障排除

### 常见问题

1. **ImportError: No module named 'app'**
   ```bash
   cd backend
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   pytest
   ```

2. **RuntimeError: Event loop is closed**
   确保使用 `pytest-asyncio` 并在 `conftest.py` 中正确配置 `event_loop` fixture。

3. **Database connection error**
   测试使用内存 SQLite，确保安装了 `aiosqlite`：
   ```bash
   pip install aiosqlite
   ```
