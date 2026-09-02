# AI 智能会议纪要系统

当前代码处于 **Phase 1 Task 2**：工程骨架、Docker、健康检查，以及 User 数据库基础、Alembic、Argon2id 和 `create_admin` CLI。尚未实现 JWT、登录 API、会议、腾讯会议接入、LLM 或 AI 纪要业务。

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

## 配置

复制配置模板后，按本地环境需要调整：

```powershell
Copy-Item .env.example .env
```

`.env` 已被 Git 忽略；不要提交真实密码或后续阶段的 Secret。

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
- Frontend：`http://localhost:5173`

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

## 停止服务

```powershell
docker compose down
```

如需同时删除 MySQL 本地数据卷，请在确认数据可删除后执行 `docker compose down -v`。
