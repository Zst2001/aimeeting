# AI 智能会议纪要系统

当前代码处于 **Phase 1 Task 4**：在工程骨架、User 数据库基础、Alembic、Argon2id 和后端 JWT 认证之上，已完成前端登录、会话恢复、Token Refresh Rotation 适配与退出登录。会议、腾讯会议接入、LLM 和 AI 纪要业务尚未实现。

## 技术栈

- Frontend: Vue 3、TypeScript、Vite、Element Plus、Pinia、Vue Router、Axios
- Backend: Python 3.12、FastAPI、Pydantic v2、pydantic-settings、SQLAlchemy 2.x
- Infrastructure: MySQL 8、Redis 7、Docker Compose

## 目录结构

```text
backend/      FastAPI 应用与测试
frontend/     Vue 3 应用
docs/         已确认设计文档与阶段确认报告
deploy/       后续部署配置预留
docker-compose.yml
```

## 环境要求

- Docker Desktop / Docker Compose v2
- Python 3.12（运行本地后端测试）
- Node.js LTS（运行本地前端构建）

## 从零开始

从远程仓库取得代码后，在项目根目录创建本地配置：

```powershell
git clone https://github.com/Zst2001/aimeeting.git aimeeting
Set-Location aimeeting
Copy-Item .env.example .env
```

`.env.example` 提供仅用于本地开发的占位配置。生产部署必须改用独立的高强度 `JWT_SECRET_KEY` 和受管 Secret；不要将 `.env` 提交到 Git。

## 配置

复制配置模板后，按本地环境需要调整：

```powershell
Copy-Item .env.example .env
```

`.env` 已被 Git 忽略；不要提交真实密码或后续阶段的 Secret。

认证所需配置：

```env
JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

生产环境必须提供独立的高强度 `JWT_SECRET_KEY`；不要使用 `.env.example` 或 Compose 中的开发占位值。

## Docker 启动

```powershell
docker compose up -d --build
docker compose ps
```

服务端口：Frontend `5173`、Backend `8000`、MySQL 容器 `3306`（宿主机默认 `3307`，可通过 `MYSQL_HOST_PORT` 调整）、Redis `6379`。

## 健康检查

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/ready
```

- `/health`：FastAPI 存活检查，不访问外部基础设施。
- `/ready`：检查 MySQL 与 Redis；任一不可用时返回 HTTP 503，且不暴露连接信息。
- FastAPI OpenAPI（开发环境）：`http://localhost:8000/docs`
- Frontend：`http://localhost:5173`（登录页：`http://localhost:5173/login`）

## 本地验证

后端：

```powershell
Set-Location backend
python -m pytest
```

前端：

```powershell
Set-Location frontend
npm ci
npm run test
npm run typecheck
npm run build
```

## 数据库 Migration

所有数据库结构变化均通过 Alembic 管理；不要使用 `Base.metadata.create_all()` 替代 Migration。

```powershell
Set-Location backend
alembic upgrade head
alembic current
alembic downgrade -1
alembic upgrade head
```

Docker 环境中执行：

```powershell
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
```

## 创建首个管理员

先完成 `alembic upgrade head`，再显式运行 CLI：

```powershell
Set-Location backend
python -m app.scripts.create_admin
```

或在 Docker 环境中运行：

```powershell
docker compose exec backend python -m app.scripts.create_admin
```

CLI 使用不回显的密码输入，并以 Argon2id 保存密码 Hash；不会写入默认管理员或明文密码。

## Backend Authentication

认证 API 均使用 `/api/v1` 前缀：

- `POST /api/v1/auth/login`：用户名和密码登录，返回 Access Token、Refresh Token 及当前用户概要。
- `POST /api/v1/auth/refresh`：使用 Refresh Token 获取新的 Token Pair；旧 Refresh Token 会立即失效。
- `POST /api/v1/auth/logout`：携带当前 Access Token，并提交 Refresh Token 以注销该会话。
- `GET /api/v1/me`：携带 `Authorization: Bearer <access_token>` 获取当前用户。

Access Token 默认有效期为 30 分钟，Refresh Token 默认有效期为 7 天。Refresh Session 只在 Redis 中保存最小化的 `user_id` 元数据，使用 `aimm:auth:refresh:{jti}` 键并随 Refresh Token 过期；V1 不实现 Access Token 黑名单，因此注销后已签发的 Access Token 最多可继续使用至其自然过期。

示例（请使用占位符，不要将真实 Token 或密码写入命令历史）：

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/v1/auth/login `
  -ContentType 'application/json' `
  -Body '{"username":"<username>","password":"<password>"}'
```

## Frontend Authentication

访问 `http://localhost:5173/login` 使用现有账号登录。前端会保存 Access Token 与 Refresh Token，并以 `/api/v1/me` 恢复刷新后的会话；当 Access Token 失效时，多个并发请求共享一次 Refresh 请求，并同时更新新的 Token Pair。退出登录会调用后端注销接口，随后无论接口结果如何都会清理浏览器本地认证状态。

V1 按既定 API 合约将 Token 存储在 `localStorage`。后续生产安全强化可评估将 Refresh Token 迁移至 `HttpOnly`、`Secure`、`SameSite` Cookie；本阶段不改变后端认证协议。

## 停止服务

```powershell
docker compose down
```

如需同时删除 MySQL 本地数据卷，请在确认数据可删除后执行 `docker compose down -v`。
