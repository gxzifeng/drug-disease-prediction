# 认证与用户管理 API 文档

## 概述

本模块提供用户认证（JWT）和用户管理（RBAC）功能。

## 认证接口 (`/api/v1/auth`)

### POST `/auth/register` - 用户注册

注册新用户账号。

**请求体：**
```json
{
  "username": "string (3-50字符，必填)",
  "email": "string (有效邮箱，必填)",
  "password": "string (6-100字符，必填)",
  "full_name": "string (可选)"
}
```

**响应示例：**
```json
{
  "code": 200,
  "message": "Registration successful",
  "data": {
    "user": {
      "id": 1,
      "username": "newuser",
      "email": "user@example.com",
      "full_name": null,
      "is_active": true,
      "is_superuser": false,
      "roles": ["user"],
      "created_at": "2026-01-10T12:00:00",
      "last_login": null
    },
    "message": "Registration successful"
  }
}
```

**错误响应：**
- `400 Bad Request`: 用户名或邮箱已被注册

---

### POST `/auth/login` - 用户登录

使用用户名和密码登录，返回访问令牌和刷新令牌。

**请求体：**
```json
{
  "username": "string",
  "password": "string"
}
```

**响应示例：**
```json
{
  "code": 200,
  "message": "Login successful",
  "data": {
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "full_name": "System Administrator",
      "is_active": true,
      "is_superuser": true,
      "roles": ["admin", "user"],
      "created_at": "2026-01-10T12:00:00",
      "last_login": "2026-01-10T13:00:00"
    },
    "token": {
      "access_token": "eyJ...",
      "refresh_token": "eyJ...",
      "token_type": "bearer",
      "expires_in": 1800
    }
  }
}
```

**错误响应：**
- `401 Unauthorized`: 用户名或密码错误

---

### POST `/auth/refresh` - 刷新令牌

使用刷新令牌获取新的访问令牌。

**请求体：**
```json
{
  "refresh_token": "string"
}
```

**响应示例：**
```json
{
  "code": 200,
  "message": "Token refreshed successfully",
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

**错误响应：**
- `401 Unauthorized`: 刷新令牌无效或已过期

---

### POST `/auth/logout` - 用户登出

撤销刷新令牌，使其失效。需要认证。

**请求体（可选）：**
```json
{
  "refresh_token": "string"
}
```

如果不提供 `refresh_token`，将撤销该用户的所有刷新令牌。

**响应示例：**
```json
{
  "code": 200,
  "message": "Logout successful",
  "data": null
}
```

---

### GET `/auth/me` - 获取当前用户信息

获取当前登录用户的详细信息。需要认证。

**响应示例：**
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "System Administrator",
    "is_active": true,
    "is_superuser": true,
    "roles": ["admin", "user"],
    "created_at": "2026-01-10T12:00:00",
    "last_login": "2026-01-10T13:00:00"
  }
}
```

---

### PUT `/auth/me` - 更新当前用户信息

更新当前用户的个人信息。需要认证。

**请求体：**
```json
{
  "email": "string (可选)",
  "full_name": "string (可选)"
}
```

**响应示例：**
```json
{
  "code": 200,
  "message": "Profile updated successfully",
  "data": {
    "id": 1,
    "username": "admin",
    "email": "newemail@example.com",
    "full_name": "New Name",
    "is_active": true,
    "is_superuser": true,
    "roles": ["admin", "user"],
    "created_at": "2026-01-10T12:00:00",
    "last_login": "2026-01-10T13:00:00"
  }
}
```

---

### PUT `/auth/me/password` - 修改密码

修改当前用户的密码。需要认证。

**请求体：**
```json
{
  "current_password": "string",
  "new_password": "string (6-100字符)"
}
```

**响应示例：**
```json
{
  "code": 200,
  "message": "Password updated successfully",
  "data": null
}
```

**错误响应：**
- `400 Bad Request`: 当前密码不正确

---

## 用户管理接口 (`/api/v1/users`) - 需要管理员权限

### GET `/users` - 获取用户列表

获取所有用户列表（分页）。需要管理员权限。

**查询参数：**
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认20，最大100）
- `is_active`: 筛选账号状态（可选）

**响应示例：**
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "items": [
      {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "System Administrator",
        "is_active": true,
        "is_superuser": true,
        "roles": ["admin", "user"],
        "created_at": "2026-01-10T12:00:00",
        "last_login": "2026-01-10T13:00:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20,
    "pages": 1
  }
}
```

---

### POST `/users` - 创建用户

创建新用户（管理员操作）。需要管理员权限。

**查询参数：**
- `roles`: 角色列表（默认 `["user"]`）

**请求体：**
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "full_name": "string (可选)"
}
```

---

### GET `/users/{user_id}` - 获取用户详情

获取指定用户的详细信息。需要管理员权限。

---

### PUT `/users/{user_id}` - 更新用户

更新指定用户的信息。需要管理员权限。

**请求体：**
```json
{
  "email": "string (可选)",
  "full_name": "string (可选)",
  "is_active": "boolean (可选)",
  "is_superuser": "boolean (可选，仅超级管理员可设置)",
  "role_ids": "[number] (可选，角色ID列表)"
}
```

---

### DELETE `/users/{user_id}` - 删除用户

删除指定用户。需要超级管理员权限。不能删除自己。

---

## 角色管理接口 (`/api/v1/users/roles`)

### GET `/users/roles/list` - 获取角色列表

获取所有角色列表。需要管理员权限。

**响应示例：**
```json
{
  "code": 200,
  "message": "Success",
  "data": [
    {
      "id": 1,
      "name": "admin",
      "description": "Administrator with full access",
      "permissions": null,
      "created_at": "2026-01-10T12:00:00"
    },
    {
      "id": 2,
      "name": "user",
      "description": "Regular user with basic access",
      "permissions": null,
      "created_at": "2026-01-10T12:00:00"
    }
  ]
}
```

---

### POST `/users/roles` - 创建角色

创建新角色。需要超级管理员权限。

---

### PUT `/users/roles/{role_id}` - 更新角色

更新角色信息。需要超级管理员权限。

---

### DELETE `/users/roles/{role_id}` - 删除角色

删除角色。需要超级管理员权限。不能删除默认角色（admin, user）。

---

## 认证方式

所有需要认证的接口都需要在请求头中携带 JWT 令牌：

```
Authorization: Bearer <access_token>
```

### 令牌有效期

- 访问令牌（Access Token）：30分钟
- 刷新令牌（Refresh Token）：7天

### 默认账号

系统初始化时会创建默认超级管理员账号：
- 用户名：`admin`
- 密码：`admin123`
- 邮箱：`admin@example.com`

**⚠️ 生产环境请务必修改默认密码！**

---

## 错误响应格式

```json
{
  "code": 400,
  "message": "错误描述",
  "errors": [
    {
      "field": "username",
      "message": "用户名已被注册"
    }
  ]
}
```

### 常见错误码

| HTTP状态码 | 说明 |
|-----------|------|
| 400 | 请求参数错误 |
| 401 | 未认证或令牌无效 |
| 403 | 无权限访问 |
| 404 | 资源不存在 |
| 422 | 数据验证失败 |
| 500 | 服务器内部错误 |
