# 修复说明

## 问题描述
在尝试启动项目时，`backend` 服务的构建过程失败，原因是 `requirements.txt` 中的依赖版本存在冲突：
- `pytest==8.0.0`
- `pytest-asyncio==0.23.4` (或 0.23.5)

错误信息提示 `pytest-asyncio` 需要 `pytest<8`。

## 解决方案
已修改 `backend/requirements.txt`，将 `pytest` 版本降级为稳定的 `7.4.4`，以确保与 `pytest-asyncio` 兼容。

变更后的依赖：
```text
pytest==7.4.4
pytest-asyncio==0.23.5
```

## 如何运行
双击运行项目根目录下的 `start_project.bat` 脚本，或者在终端执行：

```bash
docker-compose up -d --build
```
