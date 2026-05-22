# 部署指南

本文档说明如何将药物-疾病关联预测系统部署到生产环境。

## 目录

1. [部署架构](#部署架构)
2. [Docker 部署](#docker-部署)
3. [手动部署](#手动部署)
4. [配置说明](#配置说明)
5. [安全加固](#安全加固)
6. [监控与日志](#监控与日志)
7. [备份与恢复](#备份与恢复)

## 部署架构

```
                    ┌─────────────┐
                    │   Nginx     │
                    │ (反向代理)   │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
    │  Frontend │    │  Backend  │    │   WebSocket│
    │  (Vue3)   │    │ (FastAPI) │    │   (可选)   │
    └───────────┘    └─────┬─────┘    └───────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
    │   MySQL   │    │   Redis   │    │  Celery   │
    │ (数据库)   │    │  (缓存)   │    │ (异步任务) │
    └───────────┘    └───────────┘    └───────────┘
```

## Docker 部署

### 1. 准备环境

```bash
# 安装 Docker 和 Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt install docker-compose
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# 数据库配置
MYSQL_USER=root
MYSQL_PASSWORD=your_secure_password
MYSQL_DB=drug_disease_db

# Redis 配置
REDIS_URL=redis://redis:6379/0

# 后端配置
SECRET_KEY=your_very_long_and_secure_secret_key
DEBUG=false
CORS_ORIGINS=https://yourdomain.com

# 前端配置
VITE_API_BASE_URL=https://yourdomain.com/api
```

### 3. 构建并启动

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 4. Docker Compose 配置

```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_PASSWORD}
      - MYSQL_DATABASE=${MYSQL_DB}
    volumes:
      - mysql_data:/var/lib/mysql
    command: --default-authentication-plugin=mysql_native_password --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p${MYSQL_PASSWORD}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - MYSQL_HOST=mysql
      - MYSQL_PORT=3306
      - MYSQL_USER=${MYSQL_USER}
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
      - MYSQL_DB=${MYSQL_DB}
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=${DEBUG}
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./data:/app/data
      - ./models:/app/models
      - ./embeddings:/app/embeddings

  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.core.celery_app worker --loglevel=info
    environment:
      - MYSQL_HOST=mysql
      - MYSQL_PORT=3306
      - MYSQL_USER=${MYSQL_USER}
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
      - MYSQL_DB=${MYSQL_DB}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - backend
      - redis
    volumes:
      - ./data:/app/data
      - ./models:/app/models
      - ./embeddings:/app/embeddings

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      - VITE_API_BASE_URL=${VITE_API_BASE_URL}

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - backend
      - frontend

volumes:
  mysql_data:
  redis_data:
```

## 手动部署

### 1. 安装依赖

```bash
# 系统依赖
sudo apt update
sudo apt install python3.11 python3.11-venv nodejs npm mysql-server redis-server nginx

# Python 依赖
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# Node.js 依赖
cd ../frontend
npm install
npm run build
```

### 2. 配置数据库

```bash
sudo mysql -u root -p
CREATE DATABASE drug_disease_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'drugdisease'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON drug_disease_db.* TO 'drugdisease'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. 运行迁移

```bash
cd backend
alembic upgrade head
```

### 4. 配置 Systemd 服务

**后端服务 `/etc/systemd/system/drugdisease-backend.service`:**

```ini
[Unit]
Description=Drug Disease Backend
After=network.target mysql.service redis.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/drugdisease/backend
Environment="PATH=/opt/drugdisease/backend/venv/bin"
EnvironmentFile=/opt/drugdisease/.env
ExecStart=/opt/drugdisease/backend/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**Celery 服务 `/etc/systemd/system/drugdisease-celery.service`:**

```ini
[Unit]
Description=Drug Disease Celery Worker
After=network.target redis.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/drugdisease/backend
Environment="PATH=/opt/drugdisease/backend/venv/bin"
EnvironmentFile=/opt/drugdisease/.env
ExecStart=/opt/drugdisease/backend/venv/bin/celery -A app.core.celery_app worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

**启动服务：**

```bash
sudo systemctl daemon-reload
sudo systemctl enable drugdisease-backend drugdisease-celery
sudo systemctl start drugdisease-backend drugdisease-celery
```

### 5. 配置 Nginx

```nginx
upstream backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;

    # 前端静态文件
    location / {
        root /opt/drugdisease/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 文件上传大小限制
    client_max_body_size 100M;
}
```

## 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SECRET_KEY` | JWT 签名密钥 | - |
| `DATABASE_URL` | 数据库连接字符串 | - |
| `REDIS_URL` | Redis 连接字符串 | redis://localhost:6379/0 |
| `DEBUG` | 调试模式 | false |
| `CORS_ORIGINS` | 允许的跨域来源 | * |
| `MAX_UPLOAD_SIZE` | 最大上传文件大小 | 104857600 (100MB) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 过期时间 | 30 |

### 资源建议

| 部署规模 | CPU | 内存 | 存储 |
|----------|-----|------|------|
| 开发/测试 | 2 核 | 4GB | 20GB |
| 小型生产 | 4 核 | 8GB | 50GB |
| 中型生产 | 8 核 | 16GB | 100GB |
| 大型生产 | 16 核 | 32GB | 500GB |

## 安全加固

### 1. 密钥管理

```bash
# 生成强密钥
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. 数据库安全

```sql
-- 限制数据库用户权限
REVOKE ALL PRIVILEGES ON drug_disease_db.* FROM 'drugdisease'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON drug_disease_db.* TO 'drugdisease'@'localhost';
FLUSH PRIVILEGES;
```

### 3. 防火墙配置

```bash
# 只允许必要端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 4. 定期更新

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 更新 Python 依赖
pip install --upgrade -r requirements.txt
```

## 监控与日志

### 应用日志

```bash
# 查看后端日志
journalctl -u drugdisease-backend -f

# 查看 Celery 日志
journalctl -u drugdisease-celery -f

# 查看 Nginx 日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### 健康检查

```bash
# API 健康检查
curl http://localhost:8000/api/v1/health

# 数据库连接检查
mysql -u drugdisease -p drug_disease_db -e "SELECT 1"

# Redis 连接检查
redis-cli ping
```

### Prometheus 指标（可选）

安装 `prometheus-fastapi-instrumentator` 后，指标可在 `/metrics` 端点获取。

## 备份与恢复

### 数据库备份

```bash
# 备份
mysqldump -u drugdisease -p drug_disease_db > backup_$(date +%Y%m%d).sql

# 恢复
mysql -u drugdisease -p drug_disease_db < backup_20240101.sql
```

### 模型文件备份

```bash
# 备份模型和嵌入文件
tar -czvf models_backup_$(date +%Y%m%d).tar.gz models/ embeddings/
```

### 自动备份脚本

```bash
#!/bin/bash
# /opt/drugdisease/backup.sh

BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d)

# 数据库备份
mysqldump -u drugdisease -p drug_disease_db | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# 文件备份
tar -czvf $BACKUP_DIR/files_$DATE.tar.gz \
    /opt/drugdisease/models \
    /opt/drugdisease/embeddings \
    /opt/drugdisease/data/uploads

# 清理 30 天前的备份
find $BACKUP_DIR -type f -mtime +30 -delete
```

添加到 crontab：

```bash
0 2 * * * /opt/drugdisease/backup.sh
```
